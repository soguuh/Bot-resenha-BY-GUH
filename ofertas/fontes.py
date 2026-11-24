"""
Fontes — registro central das lojas. Nenhum outro módulo
importa lojas diretamente; tudo passa pelo REGISTRO_LOJAS.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from ofertas.base import Produto, StatusLoja
from ofertas.lojas.mercado_livre import MercadoLivre
from ofertas.lojas.aliexpress import AliExpress
from ofertas.lojas.shopee import Shopee
from ofertas.lojas.casas_bahia import CasasBahia
from ofertas.lojas.pichau import Pichau
from ofertas.lojas.kabum import Kabum
from ofertas.lojas.terabyte import Terabyte

logger = logging.getLogger(__name__)


class FonteDeOfertas:
    nome: str = "desconhecida"
    status: StatusLoja = StatusLoja.ATIVA

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        raise NotImplementedError

    def disponivel(self) -> bool:
        return True


REGISTRO_LOJAS: Dict[str, Type[FonteDeOfertas]] = {
    "mercado_livre": MercadoLivre,
    "aliexpress":    AliExpress,
    "shopee":        Shopee,
    "casas_bahia":   CasasBahia,
    "pichau":        Pichau,
    "kabum":         Kabum,
    "terabyte":      Terabyte,
}


def get_loja(nome: str) -> Optional[FonteDeOfertas]:
    classe = REGISTRO_LOJAS.get(nome.lower().strip())
    if classe is None:
        logger.warning("Loja não registrada: %s", nome)
        return None
    return classe()


def get_lojas_ativas() -> List[FonteDeOfertas]:
    return [cls() for cls in REGISTRO_LOJAS.values()
            if cls.status == StatusLoja.ATIVA]


def listar_lojas() -> List[dict]:
    return [
        {"nome": cls.nome, "status": cls.status.value,
         "busca_ok": cls.status == StatusLoja.ATIVA}
        for cls in REGISTRO_LOJAS.values()
    ]


def buscar_em_todas(termo: str, limite_por_loja: int = 10) -> List[Produto]:
    resultados: List[Produto] = []
    for loja in get_lojas_ativas():
        try:
            produtos = loja.buscar(termo, limite=limite_por_loja)
            resultados.extend(produtos)
            logger.info("[%s] %d produtos para '%s'", loja.nome, len(produtos), termo)
        except Exception as exc:
            logger.error("[%s] falha ao buscar '%s': %s", loja.nome, termo, exc)
    return resultados
