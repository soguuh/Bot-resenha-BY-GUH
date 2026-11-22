import json
import random
from pathlib import Path

import discord
from discord.ext import commands

WORDS_FILE = Path(__file__).resolve().parent / "dados" / "mimica.json"


def carregar_palavras():
    try:
        with WORDS_FILE.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"palavras": ["astronauta", "elefante", "guitarra", "avião"]}


class Mimica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partidas = {}

    @commands.command(name="mimica")
    async def mimica(self, ctx):
        """Inicia uma rodada de mímica; a palavra é enviada por mensagem privada."""
        if ctx.channel.id in self.partidas:
            return await ctx.send("Já existe uma rodada de mímica neste canal.")

        palavras = carregar_palavras().get("palavras", [])
        if not palavras:
            return await ctx.send("O banco de palavras da mímica está vazio.")

        palavra = random.choice(palavras)
        try:
            await ctx.author.send(
                f"🎭 **Sua palavra da mímica é:** ||{palavra}||\n"
                "Faça gestos sem falar ou escrever a palavra. As outras pessoas tentam adivinhar no canal."
            )
        except discord.Forbidden:
            return await ctx.send(
                f"{ctx.author.mention}, não consegui enviar sua palavra por DM. "
                "Ative mensagens privadas deste servidor e tente novamente."
            )

        self.partidas[ctx.channel.id] = {
            "ator": ctx.author.id,
            "palavra": palavra.lower(),
            "canal": ctx.channel
        }
        await ctx.send(
            f"🎭 **MÍMICA INICIADA!** {ctx.author.mention} está fazendo a mímica.\n"
            "As respostas devem ser enviadas neste canal. Use `/fim_mimica` para encerrar."
        )

    @commands.command(name="fim_mimica")
    async def fim_mimica(self, ctx):
        partida = self.partidas.get(ctx.channel.id)
        if not partida:
            return await ctx.send("Não existe uma mímica ativa neste canal.")
        if ctx.author.id != partida["ator"]:
            return await ctx.send("Somente quem está fazendo a mímica pode encerrar a rodada.")
        self.partidas.pop(ctx.channel.id, None)
        await ctx.send(f"🎭 A palavra era **{partida['palavra']}**.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        partida = self.partidas.get(message.channel.id)
        if not partida or message.author.id == partida["ator"]:
            return
        tentativa = message.content.strip().casefold()
        if tentativa == partida["palavra"].casefold():
            self.partidas.pop(message.channel.id, None)
            await message.channel.send(
                f"🎉 {message.author.mention} acertou a mímica! "
                f"A palavra era **{partida['palavra']}**."
            )
            if hasattr(self.bot, "adicionar_xp"):
                self.bot.adicionar_xp(message.author.id, 25)
                self.bot.adicionar_xp(partida["ator"], 10)


async def setup(bot):
    await bot.add_cog(Mimica(bot))
