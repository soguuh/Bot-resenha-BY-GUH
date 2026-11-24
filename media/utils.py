
import asyncio
import io
import ipaddress
import os
import re
import shutil
import socket
import subprocess
import tempfile

from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib.parse import urljoin

import aiohttp
from PIL import Image


TIMEOUT = aiohttp.ClientTimeout(total=120)
TAMANHO_MAXIMO_DOWNLOAD = 100 * 1024 * 1024  # 100 MB

EXTENSOES_AUDIO = {
    ".mp3", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".flac"
}

EXTENSOES_VIDEO = {
    ".mp4", ".webm", ".mov", ".mkv", ".avi"
}


def nome_seguro(nome: str) -> str:
    nome = Path(unquote(nome)).name
    nome = re.sub(r"[^a-zA-Z0-9._ -]", "_", nome)
    return nome[:100] or "arquivo"


async def validar_link(url: str) -> bool:
    """Aceita somente links HTTP/HTTPS com endereço público."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        porta = parsed.port or (443 if parsed.scheme == "https" else 80)

        loop = asyncio.get_running_loop()

        resultados = await loop.getaddrinfo(
            parsed.hostname,
            porta,
            type=socket.SOCK_STREAM
        )

        if not resultados:
            return False

        for resultado in resultados:
            endereco = ipaddress.ip_address(resultado[4][0])

            if not endereco.is_global:
                return False

        return True

    except Exception:
        return False



async def baixar_arquivo(url: str, limite: int, tipo: str):
    """
    Baixa arquivos diretos de áudio ou vídeo.
    Segue redirecionamentos HTTP com validação de destino.
    """

    if tipo == "audio":
        extensoes = EXTENSOES_AUDIO
        prefixo = "audio/"
    elif tipo == "video":
        extensoes = EXTENSOES_VIDEO
        prefixo = "video/"
    else:
        raise ValueError("Tipo de arquivo não permitido.")

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:

        url_atual = url
        response = None

        try:
            # Segue redirecionamentos manualmente.
            for _ in range(6):

                if not await validar_link(url_atual):
                    raise ValueError(
                        "O link ou seu redirecionamento possui "
                        "um endereço não permitido."
                    )

                response = await session.get(
                    url_atual,
                    allow_redirects=False
                )

                if response.status in (301, 302, 303, 307, 308):
                    destino = response.headers.get("Location")
                    response.release()

                    if not destino:
                        raise ValueError(
                            "Redirecionamento sem endereço de destino."
                        )

                    url_atual = urljoin(url_atual, destino)
                    continue

                if response.status != 200:
                    raise ValueError(
                        "O servidor não disponibilizou o arquivo. "
                        f"Status HTTP: {response.status}"
                    )

                break

            else:
                raise ValueError(
                    "O link possui redirecionamentos demais."
                )

            parsed = urlparse(url_atual)

            content_type = response.headers.get(
                "Content-Type", ""
            ).split(";")[0].strip().lower()

            extensao = Path(
                unquote(parsed.path)
            ).suffix.lower()

            mime_extensoes = {
                "audio/mpeg": ".mp3",
                "audio/mp3": ".mp3",
                "audio/wav": ".wav",
                "audio/ogg": ".ogg",
                "audio/opus": ".opus",
                "audio/mp4": ".m4a",
                "audio/aac": ".aac",
                "audio/flac": ".flac",
                "video/mp4": ".mp4",
                "video/webm": ".webm",
                "video/quicktime": ".mov",
                "video/x-matroska": ".mkv",
            }

            extensao_valida = extensao in extensoes
            mime_valido = content_type.startswith(prefixo)

            if not extensao_valida and not mime_valido:
                raise ValueError(
                    "O endereço final não disponibilizou um "
                    f"arquivo de {tipo}."
                )

            tamanho = response.content_length

            if tamanho and tamanho > TAMANHO_MAXIMO_DOWNLOAD:
                raise ValueError("O arquivo ultrapassa 100 MB.")

            dados = bytearray()

            async for parte in response.content.iter_chunked(64 * 1024):
                dados.extend(parte)

                if len(dados) > TAMANHO_MAXIMO_DOWNLOAD:
                    raise ValueError("O arquivo ultrapassa 100 MB.")

            nome = nome_seguro(
                Path(unquote(parsed.path)).name
            )

            if not Path(nome).suffix:
                extensao_final = (
                    extensao
                    if extensao_valida
                    else mime_extensoes.get(content_type)
                )

                if not extensao_final:
                    raise ValueError(
                        "Não foi possível identificar a extensão."
                    )

                nome += extensao_final

            return bytes(dados), nome

        finally:
            if response is not None:
                response.release()



def comprimir_video(dados: bytes, limite: int):
    """
    Comprime vídeos usando FFmpeg 9.1.
    Retorna os bytes comprimidos e o nome do arquivo.
    """

    ## procura primeiro o PATH do windows.

    ffmpeg = shutil.which("ffmpeg")

    ## se nao encontrar, procura na instalacao do Winget.
    if not ffmpeg:
        local_appdata = os.environ.get("LOCALAPPDATA")

        if local_appdata:
            caminho_winget = (
                Path(local_appdata)
                / "Microsoft"
                / "WinGet"
                / "Packages"
                / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
                / "ffmpeg-9.1-full_build"
                / "bin"
                / "ffmpeg.exe"
            )

            if caminho_winget.exists():
                ffmpeg = str(caminho_winget)

    if not ffmpeg:
        raise RuntimeError("FFmpeg não encontrado.")

    with tempfile.TemporaryDirectory() as pasta:

        entrada = Path(pasta) / "entrada_video.mp4"
        saida = Path(pasta) / "video_comprimido.mp4"

        entrada.write_bytes(dados)

        comando = [
            ffmpeg,
            "-y",
            "-i", str(entrada),
            "-vf", "scale='min(1280,iw)':-2",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "96k",
            "-movflags", "+faststart",
            str(saida)
        ]

        try:

            resultado = subprocess.run(
                comando,
                capture_output=True,
                timeout=180
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                "A compressão demorou demais e foi interrompida."
            )

        if resultado.returncode != 0 or not saida.exists():
            raise RuntimeError(
                "O FFmpeg não conseguiu comprimir esse vídeo."
            )

        if saida.stat().st_size > limite:
            raise ValueError(
                "Mesmo após a compressão, o vídeo continua maior "
                "que o limite de upload do servidor."
            )

        return saida.read_bytes(), "video_comprimido.mp4"



def criar_figurinha(imagem_bytes: bytes) -> bytes:
    """Converte imagem para WebP quadrado e otimizado."""

    try:
        with Image.open(io.BytesIO(imagem_bytes)) as imagem:

            imagem.load()
            imagem = imagem.convert("RGBA")

            imagem.thumbnail(
                (512, 512),
                Image.Resampling.LANCZOS
            )

            quadro = Image.new(
                "RGBA",
                (512, 512),
                (0, 0, 0, 0)
            )

            x = (512 - imagem.width) // 2
            y = (512 - imagem.height) // 2

            quadro.alpha_composite(imagem, (x, y))

            qualidade = 85

            while qualidade >= 25:

                saida = io.BytesIO()

                quadro.save(
                    saida,
                    format="WEBP",
                    quality=qualidade,
                    method=6
                )

                dados = saida.getvalue()

                if len(dados) <= 500 * 1024:
                    return dados

                qualidade -= 10

            if len(dados) > 500 * 1024:
                raise ValueError(
                    "Não foi possível reduzir a imagem para o tamanho desejado."
                )

            return dados

    except Image.DecompressionBombError:
        raise ValueError("Essa imagem é grande demais para ser processada.")

    except Image.UnidentifiedImageError:
        raise ValueError("O arquivo enviado não é uma imagem válida.")
