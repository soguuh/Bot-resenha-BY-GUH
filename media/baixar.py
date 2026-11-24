import asyncio
import io
import discord
from discord import app_commands
from discord.ext import commands
from .utils import baixar_arquivo, criar_figurinha

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

    @baixar.command(name="audio", description="Baixa áudio de links (YT, Spotify, etc)")
    @app_commands.describe(link="Link do conteúdo")
    async def audio(self, interaction: discord.Interaction, link: str):
        await interaction.response.defer(thinking=True)
        try:
            limite = self.obter_limite(interaction)
            # Agora ele realmente baixa, não apenas consulta
            dados, nome = await baixar_arquivo(link, limite, "audio")
            
            if len(dados) > limite:
                return await interaction.followup.send("❌ O arquivo de áudio excede o limite de upload do servidor.")

            arquivo = discord.File(io.BytesIO(dados), filename=nome)
            await interaction.followup.send(content="🎵 **Áudio pronto!**", file=arquivo)
        except Exception as e:
            await interaction.followup.send(f"❌ **Erro ao baixar áudio:**\n`{e}`")

    @baixar.command(name="video", description="Baixa vídeo de links")
    @app_commands.describe(link="Link do conteúdo")
    async def video(self, interaction: discord.Interaction, link: str):
        await interaction.response.defer(thinking=True)
        try:
            limite = self.obter_limite(interaction)
            dados, nome = await baixar_arquivo(link, limite, "video")
            
            if len(dados) > limite:
                return await interaction.followup.send("❌ O vídeo é muito grande para o limite do Discord.")

            arquivo = discord.File(io.BytesIO(dados), filename=nome)
            await interaction.followup.send(content="🎬 **Vídeo pronto!**", file=arquivo)
        except Exception as e:
            await interaction.followup.send(f"❌ **Erro ao baixar vídeo:**\n`{e}`")

    @baixar.command(name="figurinha", description="Transforma imagem em figurinha")
    @app_commands.describe(imagem="Imagem para a figurinha")
    async def figurinha(self, interaction: discord.Interaction, imagem: discord.Attachment):
        await interaction.response.defer(thinking=True)
        try:
            if not imagem.content_type or not imagem.content_type.startswith("image/"):
                raise ValueError("Envie uma imagem válida.")

            imagem_bytes = await imagem.read()
            figurinha_bytes = await criar_figurinha(imagem_bytes)

            arquivo = discord.File(io.BytesIO(figurinha_bytes), filename="figurinha.webp")
            await interaction.followup.send(content="✨ **Figurinha pronta!**", file=arquivo)
        except Exception as e:
            await interaction.followup.send(f"❌ **Erro na figurinha:**\n`{e}`")

async def setup(bot):
    await bot.add_cog(Baixar(bot))
