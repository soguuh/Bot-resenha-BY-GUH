"""
Mercado Livre — API pública oficial, sem chave necessária.
"""
from __future__ import annotations

import logging
from typing import List

from ofertas.base import Produto, StatusLoja
from ofertas.http_seguro import http_get

logger = logging.getLogger(__name__)


class MercadoLivre:
    nome = "mercado_livre"
    status = StatusLoja.ATIVA

    API_URL = "https://api.mercadolibre.com/sites/MLB/search"

    def buscar(self, termo: str, limite: int = 10) -> List[Produto]:
        resposta = http_get(
            self.API_URL,
            params={"q": termo, "limit": limite},
            fonte=self.nome,
        )
        dados = resposta.json()

        produtos = []
        for item in dados.get("results", []):
            produtos.append(Produto(
                loja=self.nome,
                id_produto=str(item["id"]),
                nome=item["title"],
                preco=float(item["price"]),
                url=item["permalink"],
                disponivel=item.get("available_quantity", 1) > 0,
                url_imagem=item.get("thumbnail", "").replace("http://", "https://"),
            ))
        return produtos

    def disponivel(self) -> bool:
        try:
            r = http_get(self.API_URL, params={"q": "teste", "limit": 1},
                         fonte=self.nome, use_cache=False)
            return r.status_code == 200
        except Exception:
            return False
