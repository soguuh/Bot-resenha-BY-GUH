"""
KaBuM! — verificar fonte autorizada (afiliados via Awin/Lomadee).
⚠️ Evitar scraping direto: KaBuM bloqueia agressivamente (403).
"""
from __future__ import annotations

import logging
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class Kabum:
    nome = "kabum"
    status = StatusLoja.SEM_ACESSO

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        raise NotImplementedError("Verificar fonte autorizada (afiliados KaBuM)")

    def disponivel(self) -> bool:
        return False
