"""
Monitor — loop automático multi-servidor.

A cada ciclo: consulta os preços UMA vez só e distribui
os resultados para o canal configurado de cada servidor.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

import discord
from discord.ext import commands, tasks

from ofertas.precos import MonitoradorDePrecos
from ofertas.banco import listar_canais_ofertas

logger = logging.getLogger(__name__)

# Termos monitorados para todos os servidores (ediTE à vontade)
TERMOS_MONITORADOS = [
    "iphone 15",
    "rtx 4060",
    "ssd nvme 1tb",
    "fone bluetooth",
]


class MonitorPreco(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.monitorador = MonitoradorDePrecos(margem_alerta=5.0)
        self.ultima_checagem = None
        self.monitorar.start()

    def cog_unload(self):
        self.monitorar.cancel()

    @tasks.loop(minutes=30)
    async def monitorar(self):
        # 1. Servidores configurados (quem usou !setofertas)
        configuracoes = listar_canais_ofertas()
        if not configuracoes:
            return

        # 2. Consulta os dados UMA vez só para todos
        mensagens_globais: list = []   # variações → todos os servidores
        alertas_por_guild: dict = defaultdict(list)  # alertas → só quem criou

        for termo in TERMOS_MONITORADOS:
            try:
                variacoes = await asyncio.to_thread(
                    self.monitorador.monitorar_termo, termo
                )
                mensagens_globais.extend(v.resumo() for v in variacoes)
            except Exception:
                logger.exception("Falha ao monitorar '%s'", termo)

        try:
            alertas = await asyncio.to_thread(self.monitorador.checar_alertas)
            for alerta in alertas:
                alertas_por_guild[alerta.guild_id].append(alerta.mensagem)
        except Exception:
            logger.exception("Falha ao checar alertas")

        self.ultima_checagem = discord.utils.utcnow()

        if not mensagens_globais and not alertas_por_guild:
            return  # nada mudou — silêncio

        # 3. Distribui para cada servidor
        for guild_id, canal_id in configuracoes:
            canal = self.bot.get_channel(canal_id)
            if canal is None:
                logger.warning("Canal %s não encontrado (guild %s)", canal_id, guild_id)
                continue
            try:
                for msg in mensagens_globais:
                    await canal.send(msg)
                for msg in alertas_por_guild.get(guild_id, []):
                    await canal.send(msg)
            except discord.Forbidden:
                logger.warning("Sem permissão para falar no canal %s", canal_id)
            except discord.HTTPException as exc:
                logger.error("Erro ao enviar no canal %s: %s", canal_id, exc)

    @monitorar.before_loop
    async def antes_do_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(MonitorPreco(bot))
