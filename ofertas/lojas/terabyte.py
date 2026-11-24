"""
Terabyte — verificar fonte autorizada. Endpoint JSON do site
costuma funcionar com headers corretos e rate limit respeitado.
"""
from __future__ import annotations

import logging
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class Terabyte:
    nome = "terabyte"
    status = StatusLoja.SEM_ACESSO

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        raise NotImplementedError("Verificar fonte autorizada (Terabyte)")

    def disponivel(self) -> bool:
        return False
