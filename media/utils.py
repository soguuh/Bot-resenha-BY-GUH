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
from urllib.parse import urlparse, unquote, urljoin

import aiohttp
from PIL import Image
from yt_dlp import YoutubeDL

# Configurações Globais
TIMEOUT = aiohttp.ClientTimeout(total=120)
TAMANHO_MAXIMO_DOWNLOAD = 100 * 1024 * 1024  # 100 MB

EXTENSOES_AUDIO = {".mp3", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".flac"}
EXTENSOES_VIDEO = {".mp4", ".webm", ".mov", ".mkv", ".avi"}

def nome_seguro(nome: str) -> str:
    nome = Path(unquote(nome)).name
    nome = re.sub(r"[^a-zA-Z0-9._ -]", "_", nome)
    return nome[:100] or "arquivo"

async def validar_link(url: str) -> bool:
    """Valida se o link é HTTP/HTTPS e possui IP público para evitar SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False

        porta = parsed.port or (443 if parsed.scheme == "https" else 80)
        loop = asyncio.get_running_loop()
        resultados = await loop.getaddrinfo(parsed.hostname, porta, type=socket.SOCK_STREAM)

        for resultado in resultados:
            endereco = ipaddress.ip_address(resultado[4][0])
            if not endereco.is_global:
                return False
        return True
    except Exception:
        return False

async def baixar_arquivo(url: str, limite: int, tipo: str):
    """
    Motor Híbrido de Download:
    1. Tenta baixar via yt-dlp (funciona em YT, Spotify, SoundCloud, etc).
    2. Se falhar ou for link direto, usa a lógica de stream aiohttp.
    """
    
    # --- TENTATIVA 1: YT-DLP (Para plataformas e sites complexos) ---
    try:
        # Usamos to_thread porque o yt-dlp é síncrono
        return await asyncio.to_thread(_download_via_ytdlp, url, tipo)
    except Exception as e:
        # Se o yt-dlp falhar, tentamos o download direto (sua lógica original)
        pass

    # --- TENTATIVA 2: DOWNLOAD DIRETO (Sua lógica original aprimorada) ---
    if tipo == "audio":
        extensoes, prefixo = EXTENSOES_AUDIO, "audio/"
    elif tipo == "video":
        extensoes, prefixo = EXTENSOES_VIDEO, "video/"
    else:
        raise ValueError("Tipo de arquivo não permitido.")

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        url_atual = url
        response = None
        try:
            for _ in range(6):
                if not await validar_link(url_atual):
                    raise ValueError("Endereço não permitido ou privado.")

                response = await session.get(url_atual, allow_redirects=False)
                if response.status in (301, 302, 303, 307, 308):
                    destino = response.headers.get("Location")
                    response.release()
                    if not destino: raise ValueError("Redirecionamento sem destino.")
                    url_atual = urljoin(url_atual, destino)
                    continue
                if response.status != 200:
                    raise ValueError(f"Erro do servidor: {response.status}")
                break
            else:
                raise ValueError("Redirecionamentos excessivos.")

            parsed = urlparse(url_atual)
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            extensao = Path(unquote(parsed.path)).suffix.lower()

            if not (extensao in extensoes or content_type.startswith(prefixo)):
                raise ValueError(f"O link não contém um arquivo de {tipo} válido.")

            tamanho = response.content_length
            if tamanho and tamanho > TAMANHO_MAXIMO_DOWNLOAD:
                raise ValueError("Arquivo excede 100 MB.")

            dados = bytearray()
            async for parte in response.content.iter_chunked(64 * 1024):
                dados.extend(parte)
                if len(dados) > TAMANHO_MAXIMO_DOWNLOAD:
                    raise ValueError("Arquivo excede 100 MB.")

            nome = nome_seguro(Path(unquote(parsed.path)).name)
            if not Path(nome).suffix:
                nome += extensao if extensao else ".bin"

            return bytes(dados), nome
        finally:
            if response: response.release()

def _download_via_ytdlp(url: str, tipo: str):
    """Função interna síncrona para processar downloads via yt-dlp."""
    temp_dir = tempfile.gettempdir()
    temp_name = f"dropzin_{os.urandom(4).hex()}"
    
    ydl_opts = {
        'outtmpl': f'{temp_dir}/{temp_name}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
    }

    if tipo == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif tipo == "video":
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        })

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        if tipo == "audio":
            filename = filename.rsplit('.', 1)[0] + ".mp3"
        
        with open(filename, 'rb') as f:
            data = f.read()
        
        os.remove(filename) # Limpeza imediata
        return data, os.path.basename(filename)

def comprimir_video(dados: bytes, limite: int):
    """Comprime vídeos usando FFmpeg para caber no limite do Discord."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            caminho_winget = (Path(local_appdata) / "Microsoft" / "WinGet" / "Packages" / 
                             "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / 
                             "ffmpeg-9.1-full_build" / "bin" / "ffmpeg.exe")
            if caminho_winget.exists(): ffmpeg = str(caminho_winget)

    if not ffmpeg:
        raise RuntimeError("FFmpeg não encontrado no sistema.")

    with tempfile.TemporaryDirectory() as pasta:
        entrada = Path(pasta) / "in.mp4"
        saida = Path(pasta) / "out.mp4"
        entrada.write_bytes(dados)

        comando = [
            ffmpeg, "-y", "-i", str(entrada),
            "-vf", "scale='min(1280,iw)':-2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(saida)
        ]

        try:
            subprocess.run(comando, capture_output=True, timeout=180, check=True)
        except Exception:
            raise RuntimeError("Falha na compressão do vídeo.")

        if saida.stat().st_size > limite:
            raise ValueError("Vídeo ainda é grande demais após compressão.")

        return saida.read_bytes(), "video_comprimido.mp4"

def criar_figurinha(imagem_bytes: bytes) -> bytes:
    """Converte imagem para WebP quadrado e otimizado para Discord."""
    try:
        with Image.open(io.BytesIO(imagem_bytes)) as imagem:
            imagem = imagem.convert("RGBA")
            imagem.thumbnail((512, 512), Image.Resampling.LANCZOS)

            quadro = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            x = (512 - imagem.width) // 2
            y = (512 - imagem.height) // 2
            quadro.alpha_composite(imagem, (x, y))

            qualidade = 85
            while qualidade >= 25:
                saida = io.BytesIO()
                quadro.save(saida, format="WEBP", quality=qualidade, method=6)
                dados = saida.getvalue()
                if len(dados) <= 500 * 1024: return dados
                qualidade -= 10
            
            return dados
    except Exception as e:
        raise ValueError(f"Erro ao processar imagem: {e}")
