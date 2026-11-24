
import discord
import random
import asyncio

from discord.ext import commands
from discord import app_commands


class Detetive(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.caso_atual = None

        self.casos = [
            {
                "titulo": "O Enigma do Relógio de Ouro",
                "cena": (
                    "Um milionário foi encontrado morto em sua biblioteca "
                    "trancada por dentro. O relógio de ouro no seu pulso "
                    "parou exatamente às 22:15. Há um copo de vinho "
                    "derramado e um livro aberto sobre a mesa."
                ),
                "suspeitos": {
                    "Mordomo": "Preparava o café da manhã para o dia seguinte.",
                    "Esposa": "Diz que estava dormindo no quarto ao lado.",
                    "Sócio": "Afirma que saiu da casa às 21:00."
                },
                "pistas": [
                    "O vinho contém traços de um sedativo.",
                    "O livro aberto trata de relógios antigos.",
                    "Há pegadas de lama próximas à janela."
                ],
                "culpados": ["sócio"],
                "solucao": (
                    "O Sócio. Ele mentiu sobre o horário de saída e "
                    "alterou o relógio para criar um álibi falso."
                )
            },
            {
                "titulo": "O Silêncio da Galeria",
                "cena": (
                    "Uma pintura inestimável foi roubada durante um jantar "
                    "de gala. O alarme não disparou, mas a moldura foi "
                    "deixada intacta com um bilhete: 'A arte é livre'."
                ),
                "suspeitos": {
                    "Curador": "Tinha acesso ao sistema de alarmes.",
                    "Crítico de Arte": "Passou a noite analisando as obras.",
                    "Segurança": "Diz que deu uma volta no jardim."
                },
                "pistas": [
                    "O sistema de alarmes foi desligado com um código de administrador.",
                    "O Crítico de Arte tinha manchas de tinta nas mãos.",
                    "O Segurança foi visto conversando secretamente com o Curador."
                ],
                "culpados": ["curador", "segurança"],
                "solucao": (
                    "O Curador e o Segurança agiram juntos. "
                    "O Curador desligou o alarme e o Segurança retirou a obra."
                )
            }
        ]

    @app_commands.command(
        name="detetive",
        description="Inicie uma investigação criminal."
    )
    async def detetive(self, interaction: discord.Interaction):

        self.caso_atual = random.choice(self.casos)

        embed = discord.Embed(
            title=f"🕵️ Caso: {self.caso_atual['titulo']}",
            description=(
                f"**Cena da investigação:**\n"
                f"{self.caso_atual['cena']}"
            ),
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="📋 Como investigar",
            value=(
                "`/pistas` — encontrar evidências\n"
                "`/suspeitos` — consultar suspeitos\n"
                "`/acusar` — apresentar seu veredito"
            ),
            inline=False
        )

        embed.set_footer(text="Boa investigação, detetive!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="pistas",
        description="Encontre uma pista do caso atual."
    )
    async def pistas(self, interaction: discord.Interaction):

        if not self.caso_atual:
            return await interaction.response.send_message(
                "❌ Não existe uma investigação aberta. Use `/detetive`.",
                ephemeral=True
            )

        pista = random.choice(self.caso_atual["pistas"])

        embed = discord.Embed(
            title="🔎 Evidência encontrada",
            description=f"**Nova pista:**\n{pista}",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="suspeitos",
        description="Consulte os suspeitos da investigação."
    )
    async def suspeitos(self, interaction: discord.Interaction):

        if not self.caso_atual:
            return await interaction.response.send_message(
                "❌ Não existe uma investigação aberta. Use `/detetive`.",
                ephemeral=True
            )

        texto = "\n".join(
            f"👤 **{nome}:** {descricao}"
            for nome, descricao in self.caso_atual["suspeitos"].items()
        )

        embed = discord.Embed(
            title="👥 Lista de suspeitos",
            description=texto,
            color=discord.Color.light_grey()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="acusar",
        description="Apresente seu veredito e encerre o caso."
    )
    @app_commands.describe(
        culpado="Digite o nome do suspeito que você considera culpado."
    )
    async def acusar(
        self,
        interaction: discord.Interaction,
        culpado: str
    ):

        if not self.caso_atual:
            return await interaction.response.send_message(
                "❌ Não existe uma investigação aberta. Use `/detetive`.",
                ephemeral=True
            )

        caso = self.caso_atual

        await interaction.response.send_message(
            f"⚖️ O veredito foi apresentado: **{culpado}**.\n"
            "Analisando as evidências..."
        )

        await asyncio.sleep(3)

        acusado = culpado.strip().casefold()
        acertou = acusado in caso["culpados"]

        if acertou:
            embed = discord.Embed(
                title="✅ Caso resolvido!",
                description=(
                    "Excelente investigação! Você identificou "
                    "corretamente o culpado.\n\n"
                    f"**Explicação:** {caso['solucao']}"
                ),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Veredito incorreto!",
                description=(
                    "Você não identificou corretamente os culpados.\n\n"
                    f"**A verdade:** {caso['solucao']}"
                ),
                color=discord.Color.red()
            )

        self.caso_atual = None

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Detetive(bot))
