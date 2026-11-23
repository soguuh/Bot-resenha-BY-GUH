import io

import discord
from discord import app_commands
from discord.ext import commands

from .utils import baixar_arquivo, criar_figurinha


## command download ( baixar)

class Baixar(commands.Cog):

    baixar = app_commands.Group(
        name="baixar",
        description="Baixe arquivos de mídia autorizados."
    )

    def __init__(self, bot):
        self.bot = bot

    def obter_limite(self, interaction: discord.Interaction):
        if interaction.guild:
            return interaction.guild.filesize_limit

        return 8 * 1024 * 1024

## audio 

    @baixar.command(
        name="audio",
        description="Envia um arquivo de áudio por link direto."
    )
    @app_commands.describe(
        link="Link direto do arquivo de áudio autorizado."
    )
    async def audio(
        self,
        interaction: discord.Interaction,
        link: str
    ):
        await interaction.response.defer(thinking=True)

        try:
            limite = self.obter_limite(interaction)

            dados, nome = await baixar_arquivo(
                link,
                limite,
                ("audio/",)
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
                f"❌ Não consegui enviar o áudio: {erro}",
                ephemeral=True
            )

## video 

    @baixar.command(
        name="video",
        description="Envia um arquivo de vídeo por link direto."
    )
    @app_commands.describe(
        link="Link direto do arquivo de vídeo autorizado."
    )
    async def video(
        self,
        interaction: discord.Interaction,
        link: str
    ):
        await interaction.response.defer(thinking=True)

        try:
            limite = self.obter_limite(interaction)

            dados, nome = await baixar_arquivo(
                link,
                limite,
                ("video/",)
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
                f"❌ Não consegui enviar o vídeo: {erro}",
                ephemeral=True
            )

   ## figurinha de resenha 

    @baixar.command(
        name="figurinha",
        description="Transforma uma imagem em figurinha."
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
            if not imagem.content_type or not imagem.content_type.startswith("image/"):
                raise ValueError("Envie uma imagem válida.")

            if imagem.size > 15 * 1024 * 1024:
                raise ValueError("A imagem original precisa ter até 15 MB.")

            imagem_bytes = await imagem.read()

            figurinha_bytes = criar_figurinha(imagem_bytes)

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
                f"❌ Não consegui criar a figurinha: {erro}",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Baixar(bot))