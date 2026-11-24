"""
Radar — busca de produtos em todas as lojas, deduplica,
ordena por preço e formata para o Discord.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ofertas.base import Produto
from ofertas.fontes import buscar_em_todas, get_lojas_ativas, get_loja

logger = logging.getLogger(__name__)


def _formatar_preco(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@dataclass
class ResultadoRadar:
    termo: str
    produtos: List[Produto] = field(default_factory=list)
    lojas_consultadas: int = 0
    lojas_com_erro: int = 0

    @property
    def vazio(self) -> bool:
        return not self.produtos

    def mais_barato(self) -> Optional[Produto]:
        melhores = self.melhores(1)
        return melhores[0] if melhores else None

    def melhores(self, n: int = 5) -> List[Produto]:
        disponiveis = [p for p in self.produtos if p.disponivel]
        return sorted(disponiveis, key=lambda p: p.preco)[:n]

    def por_loja(self) -> Dict[str, List[Produto]]:
        grupos: Dict[str, List[Produto]] = {}
        for p in self.produtos:
            grupos.setdefault(p.loja, []).append(p)
        return grupos

    def formatar_discord(self, max_itens: int = 5) -> str:
        if self.vazio:
            return f"🔍 Nada encontrado para **{self.termo}**."

        linhas = [f"🔍 **Resultado para:** {self.termo}", ""]

        if not [p for p in self.produtos if p.disponivel]:
            return f"🔍 Encontrei itens para **{self.termo}**, mas nenhum disponível agora."

        for p in self.melhores(max_itens):
            nome = p.nome[:70] if len(p.nome) > 70 else p.nome
            linhas.append(f"🏪 **{p.loja.replace('_', ' ').title()}**")
            linhas.append(f"📐 {nome}")
            linhas.append(f"💰 **{_formatar_preco(p.preco)}**")
            linhas.append(f"🔗 {p.url}")
            linhas.append("")

        return "\n".join(linhas)


def radar_de_precos(termo: str, limite_por_loja: int = 10) -> ResultadoRadar:
    lojas_ativas = get_lojas_ativas()
    produtos = buscar_em_todas(termo, limite_por_loja=limite_por_loja)

    lojas_com_resultado = len({p.loja for p in produtos})
    lojas_com_erro = max(0, len(lojas_ativas) - lojas_com_resultado)

    return ResultadoRadar(
        termo=termo,
        produtos=produtos,
        lojas_consultadas=lojas_com_resultado,
        lojas_com_erro=lojas_com_erro,
    )


def radar_em_loja(termo: str, nome_loja: str, limite: int = 10) -> ResultadoRadar:
    loja = get_loja(nome_loja)
    if loja is None:
        r = ResultadoRadar(termo=termo, lojas_com_erro=1)
        r.produtos = []
        return r
    try:
        produtos = loja.buscar(termo, limite=limite)
        return ResultadoRadar(termo=termo, produtos=produtos, lojas_consultadas=1)
    except Exception as exc:
        logger.error("[%s] erro: %s", nome_loja, exc)
        return ResultadoRadar(termo=termo, lojas_com_erro=1)
