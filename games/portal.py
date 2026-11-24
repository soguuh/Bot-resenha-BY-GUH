
import discord
import random

from discord.ext import commands
from discord import app_commands


class Portal(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.destinos = [
            {
                "cidade": "Tóquio",
                "pais": "Japão",
                "clima": "15°C — Nublado",
                "hora": "12:00",
                "curiosidade": (
                    "Tóquio possui uma das maiores redes ferroviárias "
                    "urbanas do mundo."
                ),
                "pergunta": "Você atravessaria o famoso cruzamento de Shibuya?"
            },
            {
                "cidade": "Reykjavík",
                "pais": "Islândia",
                "clima": "2°C — Frio",
                "hora": "08:00",
                "curiosidade": (
                    "A Islândia possui intensa atividade geotérmica "
                    "e utiliza essa energia em larga escala."
                ),
                "pergunta": "Você conseguiria passar uma semana nesse frio?"
            },
            {
                "cidade": "Cairo",
                "pais": "Egito",
                "clima": "32°C — Ensolarado",
                "hora": "10:00",
                "curiosidade": (
                    "As Pirâmides de Gizé são algumas das construções "
                    "mais famosas da Antiguidade."
                ),
                "pergunta": "Qual monumento histórico você visitaria primeiro?"
            },
            {
                "cidade": "Paris",
                "pais": "França",
                "clima": "18°C — Chuva leve",
                "hora": "14:00",
                "curiosidade": (
                    "A Torre Eiffel foi construída para a Exposição "
                    "Universal de 1889."
                ),
                "pergunta": "Você visitaria primeiro a Torre Eiffel ou o Louvre?"
            },
            {
                "cidade": "Nova York",
                "pais": "Estados Unidos",
                "clima": "10°C — Ventando",
                "hora": "05:00",
                "curiosidade": (
                    "O Central Park é um dos parques urbanos mais "
                    "conhecidos do mundo."
                ),
                "pergunta": "Você escolheria a Times Square ou o Central Park?"
            },
            {
                "cidade": "Salvador",
                "pais": "Brasil",
                "clima": "28°C — Tropical",
                "hora": "18:00",
                "curiosidade": (
                    "Salvador foi a primeira capital do Brasil "
                    "e possui um patrimônio histórico muito rico."
                ),
                "pergunta": "Qual ponto turístico de Salvador você visitaria?"
            }
        ]

    @app_commands.command(
        name="portal",
        description="Viaje para um lugar aleatório do mundo!"
    )
    async def portal(self, interaction: discord.Interaction):

        lugar = random.choice(self.destinos)

        embed = discord.Embed(
            title=f"🌍 Portal Dimensional: {lugar['cidade']}",
            description=(
                f"Você acaba de chegar a **{lugar['cidade']}, "
                f"{lugar['pais']}!**"
            ),
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🌡️ Clima",
            value=lugar["clima"],
            inline=True
        )

        embed.add_field(
            name="⏰ Horário ilustrativo",
            value=lugar["hora"],
            inline=True
        )

        embed.add_field(
            name="💡 Curiosidade",
            value=lugar["curiosidade"],
            inline=False
        )

        embed.add_field(
            name="🤔 Desafio do viajante",
            value=lugar["pergunta"],
            inline=False
        )

        embed.set_footer(
            text="Digite /portal novamente para conhecer outro destino!"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Portal(bot))
