
import asyncio
import io

import discord
from discord import app_commands
from discord.ext import commands

from .utils import (
    baixar_arquivo,
    comprimir_video,
    criar_figurinha
)

from .plataformas import (
    detectar_plataforma,
    nome_plataforma,
    obter_metadados
)


class Baixar(commands.Cog):

    baixar = app_commands.Group(
        name="baixar",
        description="Ferramentas de mídia do DROPZIN."
    )

    def __init__(self, bot):
        self.bot = bot

    def obter_limite(self, interaction: discord.Interaction):
        if interaction.guild:
            return interaction.guild.filesize_limit

        return 8 * 1024 * 1024

    async def processar_download(self, link, limite, tipo):

        plataforma = detectar_plataforma(link)

        try:
            return await baixar_arquivo(link, limite, tipo)

        except ValueError as erro:

            if plataforma:
                nome = nome_plataforma(plataforma)

                raise ValueError(
                    f"Reconheci que o link é do {nome}, mas ele não é "
                    f"um arquivo direto de {tipo}.\n\n"
                    "É necessário um arquivo disponibilizado "
                    "para download autorizado.\n\n"
                    f"Detalhe: {erro}"
                )

            raise

    async def consultar_youtube(self, interaction, link):

        dados = await obter_metadados(link)

        embed = discord.Embed(
            title=dados["titulo"],
            url=dados["url"],
            description=(
                f"**Canal:** {dados['canal']}\n"
                "**Plataforma:** YouTube"
            ),
            color=0x8B5CF6
        )

        if dados.get("thumbnail"):
            embed.set_thumbnail(url=dados["thumbnail"])

        embed.set_footer(
            text=f"DROPZIN • ID: {dados['id']}"
        )

        await interaction.followup.send(
            content=(
                "🎵 **Vídeo do YouTube reconhecido!**\n"
                "As informações foram encontradas, mas o link "
                "não é um arquivo de áudio direto. Para enviar "
                "um áudio, utilize um arquivo disponibilizado "
                "para download autorizado."
            ),
            embed=embed,
            ephemeral=True
        )

    @baixar.command(
        name="audio",
        description="Reconhece links do YouTube ou envia áudio direto."
    )
    @app_commands.describe(
        link="Link do YouTube ou link direto de um áudio autorizado."
    )
    async def audio(
        self,
        interaction: discord.Interaction,
        link: str
    ):

        await interaction.response.defer(thinking=True)

        try:
            plataforma = detectar_plataforma(link)

            if plataforma == "youtube":
                await self.consultar_youtube(interaction, link)
                return

            limite = self.obter_limite(interaction)

            dados, nome = await self.processar_download(
                link,
                limite,
                "audio"
            )

            arquivo = discord.File(
                io.BytesIO(dados),
                filename=nome
            )

            await interaction.followup.send(
                content="🎵 **Áudio pronto!**",
                file=arquivo
            )

        except Exception as erro:
            await interaction.followup.send(
                f"❌ **Não consegui processar o áudio.**\n{erro}",
                ephemeral=True
            )

    @baixar.command(
        name="video",
        description="Envia um vídeo por link, com compressão automática."
    )
    @app_commands.describe(
        link="Link direto de um vídeo disponibilizado para download."
    )
    async def video(
        self,
        interaction: discord.Interaction,
        link: str
    ):

        await interaction.response.defer(thinking=True)

        try:
            limite = self.obter_limite(interaction)

            dados, nome = await self.processar_download(
                link,
                limite,
                "video"
            )

            if len(dados) > limite:
                dados, nome = await asyncio.to_thread(
                    comprimir_video,
                    dados,
                    limite
                )

            arquivo = discord.File(
                io.BytesIO(dados),
                filename=nome
            )

            await interaction.followup.send(
                content="🎬 **Vídeo pronto!**",
                file=arquivo
            )

        except Exception as erro:
            await interaction.followup.send(
                f"❌ **Não consegui baixar o vídeo.**\n{erro}",
                ephemeral=True
            )

    @baixar.command(
        name="figurinha",
        description="Transforma uma imagem em figurinha WebP."
    )
    @app_commands.describe(
        imagem="Imagem que será transformada em figurinha."
    )
    async def figurinha(
        self,
        interaction: discord.Interaction,
        imagem: discord.Attachment
    ):

        await interaction.response.defer(thinking=True)

        try:
            if (
                not imagem.content_type
                or not imagem.content_type.startswith("image/")
            ):
                raise ValueError("Envie um arquivo de imagem válido.")

            if imagem.size > 15 * 1024 * 1024:
                raise ValueError(
                    "A imagem original pode ter no máximo 15 MB."
                )

            imagem_bytes = await imagem.read()

            figurinha_bytes = await asyncio.to_thread(
                criar_figurinha,
                imagem_bytes
            )

            arquivo = discord.File(
                io.BytesIO(figurinha_bytes),
                filename="figurinha.webp"
            )

            await interaction.followup.send(
                content="✨ **Sua figurinha está pronta!**",
                file=arquivo
            )

        except Exception as erro:
            await interaction.followup.send(
                f"❌ **Não consegui criar a figurinha.**\n{erro}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Baixar(bot))
