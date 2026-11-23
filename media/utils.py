import io
import ipaddress
import socket
from urllib.parse import urlparse
from pathlib import Path

import aiohttp
from PIL import Image


## utilitarios ae

TIMEOUT = aiohttp.ClientTimeout(total=60)


async def validar_link(url: str):
    """Aceita somente links HTTP/HTTPS públicos."""

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        loop = __import__("asyncio").get_running_loop()

        resultados = await loop.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
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


async def baixar_arquivo(url: str, limite: int, tipos_permitidos: tuple):
    """Baixa um arquivo direto, respeitando o limite de tamanho."""

    if not await validar_link(url):
        raise ValueError("Link inválido ou endereço não permitido.")

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        async with session.get(
            url,
            allow_redirects=False
        ) as response:

            if response.status != 200:
                raise ValueError("Não foi possível acessar o arquivo.")

            tipo = response.headers.get("Content-Type", "")
            tipo = tipo.split(";")[0].strip().lower()

            if not any(tipo.startswith(t) for t in tipos_permitidos):
                raise ValueError("O link não aponta para um arquivo compatível.")

            tamanho = response.content_length

            if tamanho is not None and tamanho > limite:
                raise ValueError("O arquivo ultrapassa o limite do Discord.")

            dados = bytearray()

            async for parte in response.content.iter_chunked(64 * 1024):
                dados.extend(parte)

                if len(dados) > limite:
                    raise ValueError("O arquivo ultrapassa o limite do Discord.")

            nome = Path(urlparse(url).path).name or "arquivo"

            return bytes(dados), nome


def criar_figurinha(imagem_bytes: bytes) -> bytes:
    """Converte uma imagem para WebP quadrado, pequeno e otimizado."""

    with Image.open(io.BytesIO(imagem_bytes)) as imagem:
        imagem = imagem.convert("RGBA")
        imagem.thumbnail((512, 512), Image.Resampling.LANCZOS)

        # Centraliza a imagem em um quadro transparente.
        quadro = Image.new("RGBA", (512, 512), (0, 0, 0, 0))

        x = (512 - imagem.width) // 2
        y = (512 - imagem.height) // 2

        quadro.alpha_composite(imagem, (x, y))

        qualidade = 85

        while qualidade >= 30:
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

        return dados