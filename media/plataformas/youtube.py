
from urllib.parse import urlparse, parse_qs
import aiohttp


DOMINIOS_YOUTUBE = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def reconhecer_link(url: str) -> bool:
    try:
        dominio = (urlparse(url).hostname or "").lower().rstrip(".")
        return (
            dominio in DOMINIOS_YOUTUBE
            or dominio.endswith(".youtube.com")
        )
    except Exception:
        return False


def extrair_id_video(url: str):
    if not reconhecer_link(url):
        return None

    try:
        parsed = urlparse(url)
        dominio = (parsed.hostname or "").lower()

        if dominio == "youtu.be":
            identificador = parsed.path.strip("/").split("/")[0]
        else:
            parametros = parse_qs(parsed.query)

            if "v" in parametros:
                identificador = parametros["v"][0]
            else:
                partes = parsed.path.strip("/").split("/")
                identificador = partes[-1] if partes else None

        if identificador and len(identificador) == 11:
            return identificador

        return None

    except Exception:
        return None


def url_canonica(url: str):
    identificador = extrair_id_video(url)

    if not identificador:
        return None

    return f"https://www.youtube.com/watch?v={identificador}"


async def obter_metadados(url: str):
    """
    Consulta informações públicas do vídeo.
    Não realiza download de áudio ou vídeo.
    """

    canonica = url_canonica(url)

    if not canonica:
        raise ValueError("Link de vídeo do YouTube inválido.")

    endpoint = "https://www.youtube.com/oembed"

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                endpoint,
                params={
                    "url": canonica,
                    "format": "json"
                }
            ) as resposta:

                if resposta.status != 200:
                    raise ValueError(
                        "O vídeo não está disponível para consulta "
                        "pública ou não permite incorporação."
                    )

                dados = await resposta.json()

                return {
                    "plataforma": "YouTube",
                    "id": extrair_id_video(url),
                    "titulo": dados.get("title"),
                    "canal": dados.get("author_name"),
                    "canal_url": dados.get("author_url"),
                    "thumbnail": dados.get("thumbnail_url"),
                    "url": canonica,
                }

    except aiohttp.ClientError as erro:
        raise ValueError(
            f"Erro de conexão com o YouTube: {erro}"
        ) from erro
