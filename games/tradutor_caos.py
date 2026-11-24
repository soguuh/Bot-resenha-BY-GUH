
import random
import aiohttp
import discord

from discord.ext import commands
from discord import app_commands


IDIOMAS = {
    "Espanhol": "es",
    "Francês": "fr",
    "Alemão": "de",
    "Italiano": "it",
    "Japonês": "ja",
    "Russo": "ru",
    "Turco": "tr",
    "Árabe": "ar",
    "Hindi": "hi"
}


async def traduzir(session, texto, origem, destino):

    url = "https://api.mymemory.translated.net/get"

    params = {
        "q": texto,
        "langpair": f"{origem}|{destino}"
    }

    async with session.get(
        url,
        params=params,
        timeout=aiohttp.ClientTimeout(total=20)
    ) as response:

        if response.status != 200:
            raise RuntimeError("A API de tradução está indisponível.")

        dados = await response.json()

        resultado = dados.get(
            "responseData", {}
        ).get("translatedText")

        if not resultado:
            raise RuntimeError("A API não retornou uma tradução.")

        return resultado


class TradutorCaos(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="tradutor_caos",
        description="Traduza uma frase por cinco idiomas aleatórios."
    )
    @app_commands.describe(
        frase="A frase que será transformada."
    )
    async def tradutor_caos(
        self,
        interaction: discord.Interaction,
        frase: str
    ):

        frase = frase.strip()

        if not frase or len(frase) > 400:
            return await interaction.response.send_message(
                "A frase precisa ter entre 1 e 400 caracteres.",
                ephemeral=True
            )

        await interaction.response.defer()

        idiomas = random.sample(list(IDIOMAS.items()), 5)

        atual = frase
        etapas = []

        try:
            async with aiohttp.ClientSession() as session:

                for nome, codigo in idiomas:
                    atual = await traduzir(
                        session,
                        atual,
                        "pt",
                        codigo
                    )

                    etapas.append((nome, atual))

                resultado = await traduzir(
                    session,
                    atual,
                    idiomas[-1][1],
                    "pt"
                )

            descricao = ""

            for nome, texto in etapas:
                trecho = texto[:500]
                descricao += f"**{nome}:** {trecho}\n\n"

            embed = discord.Embed(
                title="🌎 Tradutor do Caos",
                description=(
                    f"**Frase original:**\n{frase[:500]}\n\n"
                    f"{descricao}"
                    f"**🇧🇷 Tradução final:**\n{resultado[:1000]}"
                ),
                color=discord.Color.purple()
            )

            embed.set_footer(
                text="DROPZIN • Tradução automática recreativa"
            )

            await interaction.followup.send(embed=embed)

        except (aiohttp.ClientError, RuntimeError, ValueError) as erro:
            await interaction.followup.send(
                f"❌ Não consegui concluir a tradução: {erro}"
            )

        except Exception:
            await interaction.followup.send(
                "❌ Ocorreu um erro inesperado durante a tradução."
            )


async def setup(bot):
    await bot.add_cog(TradutorCaos(bot))
