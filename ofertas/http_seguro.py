"""
HTTP Seguro — camada central de requisições.

Evita erros 403/429 com: headers de navegador, rate limit
por loja, retry com backoff e cache curto.
"""
from __future__ import annotations

import logging
import random
import threading
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

HEADERS_PADRAO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

INTERVALO_POR_LOJA = 3.0            # segundos mínimos entre requisições à mesma loja
TEMPO_EXPIRACAO_CACHE = 300        # 5 minutos

_ultimo_acesso: dict = {}
_lock = threading.Lock()
_cache: dict = {}


def _respeitar_intervalo(loja: str):
    with _lock:
        agora = time.time()
        ultimo = _ultimo_acesso.get(loja, 0)
        espera = INTERVALO_POR_LOJA - (agora - ultimo)
        if espera > 0:
            time.sleep(espera)
        _ultimo_acesso[loja] = time.time()


def http_get(
    url: str,
    params: Optional[dict] = None,
    fonte: str = "generico",
    use_cache: bool = True,
    timeout: int = 15,
) -> requests.Response:
    chave_cache = f"{url}?{sorted((params or {}).items())}"

    if use_cache:
        entrada = _cache.get(chave_cache)
        if entrada and time.time() - entrada[0] < TEMPO_EXPIRACAO_CACHE:
            return entrada[1]

    _respeitar_intervalo(fonte)

    tentativas = 3
    resposta = None

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(
                url, params=params, headers=HEADERS_PADRAO, timeout=timeout
            )

            if resposta.status_code == 403:
                logger.warning("[%s] 403 (tentativa %d/%d)", fonte, tentativa, tentativas)
                time.sleep((2 ** tentativa) + random.uniform(0, 1))
                continue

            if resposta.status_code == 429:
                espera = int(resposta.headers.get("Retry-After", 10))
                logger.warning("[%s] 429 — aguardando %ds", fonte, espera)
                time.sleep(espera)
                continue

            if resposta.status_code >= 500:
                logger.warning("[%s] %d (tentativa %d/%d)",
                               fonte, resposta.status_code, tentativa, tentativas)
                time.sleep(2 ** tentativa)
                continue

            resposta.raise_for_status()

            if use_cache:
                _cache[chave_cache] = (time.time(), resposta)
            return resposta

        except requests.Timeout:
            logger.warning("[%s] timeout (tentativa %d/%d)", fonte, tentativa, tentativas)
            time.sleep(2 ** tentativa)

    # esgotou as tentativas — propaga o último erro
    if resposta is not None:
        resposta.raise_for_status()
    raise requests.ConnectionError(f"[{fonte}] falhou após {tentativas} tentativas: {url}")
