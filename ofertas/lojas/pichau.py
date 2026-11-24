"""
Pichau — verificar fonte autorizada (painel de parceiros/afiliados).
"""
from __future__ import annotations

import logging
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class Pichau:
    nome = "pichau"
    status = StatusLoja.SEM_ACESSO

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        raise NotImplementedError("Verificar fonte autorizada (parceiros Pichau)")

    def disponivel(self) -> bool:
        return False
