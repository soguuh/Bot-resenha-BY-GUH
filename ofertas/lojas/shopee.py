"""
Shopee — Open Platform / API de Afiliados (open.shopee.com.br).
Aguardando aprovação no programa. Preencher .env,
implementar buscar() e mudar status para ATIVA.
"""
from __future__ import annotations

import logging
import os
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class Shopee:
    nome = "shopee"
    status = StatusLoja.PENDENTE_API

    PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID")
    PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY")

    API_URL = "https://openplatform.shopee.com.br"

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        if not (self.PARTNER_ID and self.PARTNER_KEY):
            raise RuntimeError("Shopee: configure SHOPEE_PARTNER_ID e SHOPEE_PARTNER_KEY no .env")
        raise NotImplementedError("Implementar consulta via API Shopee")

    def gerar_link_afiliado(self, url_produto: str) -> str:
        raise NotImplementedError

    def disponivel(self) -> bool:
        return bool(self.PARTNER_ID and self.PARTNER_KEY)
