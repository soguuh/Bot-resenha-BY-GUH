"""
Casas Bahia — verificar acesso via programa de parceiros Via
(parceirosvia.com.br). Sem API pública conhecida.
"""
from __future__ import annotations

import logging
from typing import List

from ofertas.base import Produto, StatusLoja

logger = logging.getLogger(__name__)


class CasasBahia:
    nome = "casas_bahia"
    status = StatusLoja.SEM_ACESSO

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        raise NotImplementedError("Verificar acesso (parceiros Via)")

    def disponivel(self) -> bool:
        return False
