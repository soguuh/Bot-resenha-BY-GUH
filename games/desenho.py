import json
import random
from pathlib import Path

import discord
from discord.ext import commands

WORDS_FILE = Path(__file__).resolve().parent / "dados" / "mimica.json"


def carregar_desafios():
    try:
        with WORDS_FILE.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados.get("desenhos", dados.get("palavras", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return ["castelo", "dragão", "foguete", "robô"]


class Desenho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partidas = {}

    @commands.command(name="desenho")
    async def desenho(self, ctx):
        """Inicia um desafio de desenho; o tema é enviado por DM ao artista."""
        if ctx.channel.id in self.partidas:
            return await ctx.send("Já existe um desafio de desenho ativo neste canal.")

        tema = random.choice(carregar_desafios())
        try:
            await ctx.author.send(
                f"🎨 **Seu desafio é desenhar:** ||{tema}||\n"
                "Envie a imagem desenhada no canal onde iniciou o jogo."
            )
        except discord.Forbidden:
            return await ctx.send(
                f"{ctx.author.mention}, não consegui enviar o tema por DM. "
                "Ative mensagens privadas deste servidor e tente novamente."
            )

        self.partidas[ctx.channel.id] = {
            "artista": ctx.author.id,
            "tema": tema.casefold(),
            "imagem_enviada": False
        }
        await ctx.send(
            f"🎨 **DESAFIO DE DESENHO!** {ctx.author.mention} recebeu um tema secreto.\n"
            "Aguardando o desenho ser enviado como imagem ou anexo neste canal."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        partida = self.partidas.get(message.channel.id)
        if not partida:
            return

        if message.author.id == partida["artista"]:
            if message.attachments:
                partida["imagem_enviada"] = True
                await message.channel.send(
                    "🖼️ Desenho recebido! Agora os outros jogadores podem tentar adivinhar "
                    "escrevendo a resposta no canal."
                )
            return

        if partida["imagem_enviada"] and message.content.strip().casefold() == partida["tema"]:
            self.partidas.pop(message.channel.id, None)
            await message.channel.send(
                f"🎉 {message.author.mention} acertou o desenho! "
                f"O tema era **{partida['tema']}**."
            )
            if hasattr(self.bot, "adicionar_xp"):
                self.bot.adicionar_xp(message.author.id, 25)
                self.bot.adicionar_xp(partida["artista"], 10)

    @commands.command(name="fim_desenho")
    async def fim_desenho(self, ctx):
        partida = self.partidas.get(ctx.channel.id)
        if not partida:
            return await ctx.send("Não existe um desafio de desenho ativo neste canal.")
        if ctx.author.id != partida["artista"]:
            return await ctx.send("Somente o artista pode encerrar o desafio.")
        self.partidas.pop(ctx.channel.id, None)
        await ctx.send(f"🎨 O tema era **{partida['tema']}**.")


async def setup(bot):
    await bot.add_cog(Desenho(bot))
