"""
Comandos do Discord para o radar de preços.
"""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from ofertas.radar import radar_de_precos, radar_em_loja
from ofertas.fontes import listar_lojas
from ofertas.banco import (
    criar_alerta, listar_alertas_do_servidor, desativar_alerta,
    salvar_canal_ofertas, remover_canal_ofertas, obter_canal_ofertas,
)

logger = logging.getLogger(__name__)


class Ofertas(commands.Cog):
    """Consulta de preços e alertas."""

    def __init__(self, bot):
        self.bot = bot

    # ── CONSULTAS ─────────────────────────────────────────────

    @commands.command(name="preco")
    async def preco(self, ctx, *, termo: str):
        """Busca um produto nas lojas. Ex: !preco rtx 4060"""
        async with ctx.typing():
            resultado = await discord.utils.maybe_coroutine(
                _rodar, radar_de_precos, termo
            )
        await ctx.send(resultado.formatar_discord(max_itens=5))

    @commands.command(name="precoloja")
    async def precoloja(self, ctx, loja: str, *, termo: str):
        """Busca em uma loja específica. Ex: !precoloja mercado_livre rtx 4060"""
        async with ctx.typing():
            resultado = _rodar(radar_em_loja, termo, loja)
        await ctx.send(resultado.formatar_discord(max_itens=5))

    @commands.command(name="lojas")
    async def lojas(self, ctx):
        """Lista as lojas disponíveis no radar."""
        linhas = ["🏪 **Lojas no radar:**", ""]
        for loja in listar_lojas():
            icone = "✅" if loja["busca_ok"] else "⏳"
            linhas.append(f"{icone} `{loja['nome']}` — {loja['status']}")
        await ctx.send("\n".join(linhas))

    # ── ALERTAS ───────────────────────────────────────────────

    @commands.command(name="alerta")
    async def alerta(self, ctx, preco_alvo: float, *, termo: str):
        """Cria alerta de preço. Ex: !alerta 2500 rtx 4060"""
        if preco_alvo <= 0:
            await ctx.send("O preço-alvo precisa ser maior que zero.")
            return

        criar_alerta(termo, preco_alvo, guild_id=ctx.guild.id, criado_por=str(ctx.author))
        await ctx.send(
            f"🎯 **Alerta criado!**\n"
            f"Monitorando: **{termo}**\n"
            f"Vou avisar neste servidor quando custar "
            f"**R$ {preco_alvo:,.2f}** ou menos.".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    @commands.command(name="meusalertas")
    async def meusalertas(self, ctx):
        """Lista os alertas ativos deste servidor."""
        alertas = listar_alertas_do_servidor(ctx.guild.id)
        if not alertas:
            await ctx.send("Nenhum alerta ativo neste servidor. Crie com `!alerta 2500 rtx 4060`.")
            return

        linhas = ["🎯 **Alertas deste servidor:**", ""]
        for a in alertas:
            alvo = f"R$ {a.preco_alvo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            linhas.append(f"• `#{a.id_alerta}` — **{a.termo_busca}** abaixo de **{alvo}**")
        linhas.append("")
        linhas.append("Para remover: `!removeralerta <id>`")
        await ctx.send("\n".join(linhas))

    @commands.command(name="removeralerta")
    async def removeralerta(self, ctx, id_alerta: int):
        """Remove um alerta pelo ID. Ex: !removeralerta 3"""
        if desativar_alerta(id_alerta):
            await ctx.send(f"✅ Alerta `#{id_alerta}` removido.")
        else:
            await ctx.send(f"❌ Alerta `#{id_alerta}` não encontrado.")

    # ── CONFIGURAÇÃO DO SERVIDOR ──────────────────────────────

    @commands.command(name="setofertas")
    @commands.has_permissions(administrator=True)
    async def setofertas(self, ctx, canal: discord.TextChannel = None):
        """Define o canal de notificações. Ex: !setofertas #ofertas"""
        if canal is None:
            await ctx.send("Marque um canal: `!setofertas #nomedocanal`")
            return
        salvar_canal_ofertas(ctx.guild.id, canal.id)
        await ctx.send(
            f"✅ Pronto! Avisos de preço serão enviados em {canal.mention}.\n"
            f"Para parar: `!removerofertas`"
        )

    @commands.command(name="removerofertas")
    @commands.has_permissions(administrator=True)
    async def removerofertas(self, ctx):
        """Desativa as notificações neste servidor."""
        remover_canal_ofertas(ctx.guild.id)
        await ctx.send("🔕 Notificações desativadas neste servidor.")

    @commands.command(name="statusofertas")
    async def statusofertas(self, ctx):
        """Mostra a configuração deste servidor."""
        canal_id = obter_canal_ofertas(ctx.guild.id)
        parte_canal = (f"<#{canal_id}> ✅" if canal_id
                        else "não configurado — use `!setofertas #canal`")
        await ctx.send(
            f"📊 **Status das ofertas neste servidor:**\n"
            f"📣 Canal de notificações: {parte_canal}"
        )


# ── Utilidade: roda função bloqueante sem travar o bot ────────
def _rodar(func, *args, **kwargs):
    import asyncio
    return asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))


async def setup(bot):
    await bot.add_cog(Ofertas(bot))
