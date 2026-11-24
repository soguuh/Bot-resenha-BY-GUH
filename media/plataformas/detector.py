
from urllib.parse import urlparse

PLATAFORMAS = {
    "youtube_music": {
        "nome": "YouTube Music",
        "dominios": ["music.youtube.com"],
    },
    "youtube": {
        "nome": "YouTube",
        "dominios": ["youtube.com", "youtu.be"],
    },
    "spotify": {
        "nome": "Spotify",
        "dominios": ["open.spotify.com", "spotify.com"],
    },
    "soundcloud": {
        "nome": "SoundCloud",
        "dominios": ["soundcloud.com", "on.soundcloud.com"],
    },
    "bandcamp": {
        "nome": "Bandcamp",
        "dominios": ["bandcamp.com"],
    },
}


def detectar_plataforma(url: str):
    try:
        parsed = urlparse(url.strip())

        if parsed.scheme not in ("http", "https"):
            return None

        dominio = (parsed.hostname or "").lower().rstrip(".")

        for identificador, dados in PLATAFORMAS.items():
            for permitido in dados["dominios"]:
                if dominio == permitido or dominio.endswith("." + permitido):
                    return identificador

        return None

    except (ValueError, AttributeError):
        return None


def nome_plataforma(identificador: str):
    dados = PLATAFORMAS.get(identificador)
    return dados["nome"] if dados else "Desconhecida"
