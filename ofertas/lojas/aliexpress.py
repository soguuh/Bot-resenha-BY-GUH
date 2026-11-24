"""
AliExpress — API Oficial DS Open Platform (openservice.aliexpress.com).
Aguardando credenciais. Quando tiver, preencha o .env,
implemente o buscar() e mude status para ATIVA.
"""
from __future__ import annotations

import logging
import os
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class AliExpress:
    nome = "aliexpress"
    status = StatusLoja.PENDENTE_API

    API_KEY = os.getenv("ALIEXPRESS_APP_KEY")
    API_SECRET = os.getenv("ALIEXPRESS_APP_SECRET")
    ACCESS_TOKEN = os.getenv("ALIEXPRESS_ACCESS_TOKEN")

    API_URL = "https://api-sg.aliexpress.com/sync"

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        if not all([self.API_KEY, self.API_SECRET, self.ACCESS_TOKEN]):
            raise RuntimeError(
                "AliExpress: configure ALIEXPRESS_APP_KEY, "
                "ALIEXPRESS_APP_SECRET e ALIEXPRESS_ACCESS_TOKEN no .env"
            )
        raise NotImplementedError("Implementar consulta via API AliExpress")

    def disponivel(self) -> bool:
        return all([self.API_KEY, self.API_SECRET, self.ACCESS_TOKEN])
