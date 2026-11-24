
import re
import discord

from discord.ext import commands
from discord import app_commands


POSITIVAS = {
    "bom", "boa", "ótimo", "otimo", "legal", "feliz",
    "amo", "amei", "incrível", "incrivel", "perfeito",
    "kkkk", "kkk", "haha", "hahaha", "obrigado",
    "obrigada", "parabéns", "parabens", "top", "maravilhoso"
}

HOSTIS = {
    "idiota", "burro", "burra", "lixo", "odeio",
    "horrível", "horrivel", "ridículo", "ridiculo",
    "imbecil", "inútil", "inutil", "cala"
}

NEGATIVAS = {
    "triste", "cansado", "cansada", "difícil", "dificil",
    "péssimo", "pessimo", "ruim", "desanimado",
    "desanimada", "chato", "chata", "aff", "droga"
}


class Vibe(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="vibe",
        description="Analisa a energia das últimas 100 mensagens."
    )
    async def vibe(self, interaction: discord.Interaction):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "Este comando só funciona em servidores.",
                ephemeral=True
            )

        canal = interaction.channel

        permissoes = canal.permissions_for(interaction.guild.me)

        if not permissoes.read_message_history:
            return await interaction.response.send_message(
                "Preciso da permissão de ler o histórico de mensagens.",
                ephemeral=True
            )

        await interaction.response.defer()

        mensagens = []

        try:
            async for mensagem in canal.history(limit=100):
                if not mensagem.author.bot and mensagem.content:
                    mensagens.append(mensagem.content.lower())

        except discord.Forbidden:
            return await interaction.followup.send(
                "Não tenho permissão para consultar o histórico deste canal."
            )

        if not mensagens:
            return await interaction.followup.send(
                "Não encontrei mensagens suficientes para analisar."
            )

        texto = " ".join(mensagens)

        palavras = re.findall(r"\b[\wÀ-ÿ]+\b", texto)

        positivas = sum(1 for p in palavras if p in POSITIVAS)
        hostis = sum(1 for p in palavras if p in HOSTIS)
        negativas = sum(1 for p in palavras if p in NEGATIVAS)

        emojis = len(re.findall(r"<a?:\w+:\d+>", texto))
        exclamacoes = texto.count("!")

        total = positivas + hostis + negativas

        if hostis >= 3 and hostis > positivas:
            categoria = "Tóxica"
            cor = discord.Color.red()
            descricao = "A conversa apresentou vários termos hostis."

        elif negativas >= 3 and negativas > positivas:
            categoria = "Melancólica"
            cor = discord.Color.dark_grey()
            descricao = "O vocabulário negativo apareceu com mais frequência."

        elif emojis + exclamacoes >= 15:
            categoria = "Caótica"
            cor = discord.Color.orange()
            descricao = "O canal está cheio de reações e intensidade!"

        elif positivas >= negativas + hostis:
            categoria = "Chat"
            cor = discord.Color.green()
            descricao = "O vocabulário positivo predominou na conversa."

        else:
            categoria = "Neutra"
            cor = discord.Color.blurple()
            descricao = "A conversa está relativamente equilibrada."

        embed = discord.Embed(
            title=f"📊 Vibe do canal: {categoria}",
            description=descricao,
            color=cor
        )

        embed.add_field(
            name="💚 Termos positivos",
            value=str(positivas),
            inline=True
        )

        embed.add_field(
            name="⚠️ Termos hostis",
            value=str(hostis),
            inline=True
        )

        embed.add_field(
            name="🌧️ Termos negativos",
            value=str(negativas),
            inline=True
        )

        embed.add_field(
            name="😂 Emojis personalizados",
            value=str(emojis),
            inline=True
        )

        embed.add_field(
            name="❗ Exclamações",
            value=str(exclamacoes),
            inline=True
        )

        embed.add_field(
            name="💬 Mensagens analisadas",
            value=str(len(mensagens)),
            inline=True
        )

        embed.set_footer(
            text="DROPZIN • Análise textual recreativa, não psicológica"
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Vibe(bot))
