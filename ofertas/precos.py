"""
Preços — monitoramento contínuo. Compara a consulta atual
com o histórico salvo e detecta quedas/aumentos relevantes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from ofertas.base import Produto
from ofertas.banco import (
    salvar_historico, obter_ultimo_preco, listar_alertas,
)
from ofertas.radar import radar_de_precos
from ofertas.radar import _formatar_preco

logger = logging.getLogger(__name__)


@dataclass
class VariacaoPreco:
    produto: Produto
    preco_anterior: float
    variacao_reais: float
    variacao_percentual: float

    @property
    def caiu(self) -> bool:
        return self.variacao_reais < 0

    def resumo(self) -> str:
        icone = "📉" if self.caiu else "📈"
        return (
            f"{icone} **{self.produto.nome[:60]}**\n"
            f"De **{_formatar_preco(self.preco_anterior)}** por "
            f"**{_formatar_preco(self.produto.preco)}** "
            f"({self.variacao_percentual:+.1f}%)\n"
            f"🏪 {self.produto.loja.replace('_', ' ').title()} 👉 {self.produto.url}"
        )


@dataclass
class AlertaDisparado:
    """Alerta que atingiu o preço-alvo (vinculado ao servidor que o criou)."""
    guild_id: Optional[int]
    mensagem: str


class MonitoradorDePrecos:
    def __init__(self, margem_alerta: float = 5.0):
        self.margem_alerta = margem_alerta

    def verificar_variacoes(self, produtos: List[Produto]) -> List[VariacaoPreco]:
        variacoes: List[VariacaoPreco] = []

        for produto in produtos:
            # 1. salva o preço ATUAL primeiro
            salvar_historico(produto)
            # 2. busca o preço ANTERIOR ao que acabamos de salvar
            anterior = obter_ultimo_preco(produto.chave_unica)

            if anterior is None or anterior <= 0:
                continue  # primeira vez que vemos este produto

            diff = produto.preco - anterior
            percentual = (diff / anterior) * 100

            if abs(percentual) >= self.margem_alerta:
                variacoes.append(VariacaoPreco(
                    produto=produto,
                    preco_anterior=anterior,
                    variacao_reais=diff,
                    variacao_percentual=percentual,
                ))

        return variacoes

    def monitorar_termo(self, termo: str) -> List[VariacaoPreco]:
        resultado = radar_de_precos(termo)
        return self.verificar_variacoes(resultado.produtos)

    def checar_alertas(self) -> List[AlertaDisparado]:
        """
        Verifica alertas com preço-alvo (por servidor).
        Retorna mensagens prontas + o guild_id que deve recebe-las.
        """
        disparados: List[AlertaDisparado] = []

        for alerta in listar_alertas():
            if not alerta.ativo:
                continue
            try:
                resultado = radar_de_precos(alerta.termo_busca)
            except Exception:
                logger.exception("Falha ao checar alerta '%s'", alerta.termo_busca)
                continue

            barato = resultado.mais_barato()
            if barato and barato.preco <= alerta.preco_alvo:
                disparados.append(AlertaDisparado(
                    guild_id=alerta.guild_id,
                    mensagem=(
                        f"🎯 **ALERTA DE PREÇO!**\n"
                        f"Monitorando: **{alerta.termo_busca}**\n"
                        f"Alvo: {_formatar_preco(alerta.preco_alvo)}\n\n"
                        f"🏅 **{barato.nome[:60]}**\n"
                        f"💰 **{_formatar_preco(barato.preco)}**\n"
                        f"🏪 {barato.loja.replace('_', ' ').title()} 👉 {barato.url}"
                    ),
                ))
        return disparados
