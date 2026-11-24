
import discord
from discord.ext import commands
from discord import app_commands


class Confissao(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="confissao",
        description="Envie uma confissão anônima para um canal."
    )
    @app_commands.describe(
        mensagem="O texto que será publicado anonimamente",
        canal="Canal onde a confissão será publicada"
    )
    async def confissao(
        self,
        interaction: discord.Interaction,
        mensagem: str,
        canal: discord.TextChannel = None
    ):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "Este comando só funciona em servidores.",
                ephemeral=True
            )

        mensagem = mensagem.strip()

        if len(mensagem) < 3 or len(mensagem) > 1500:
            return await interaction.response.send_message(
                "A confissão precisa ter entre 3 e 1500 caracteres.",
                ephemeral=True
            )

        destino = canal or interaction.channel

        if not isinstance(destino, discord.TextChannel):
            return await interaction.response.send_message(
                "Escolha um canal de texto válido.",
                ephemeral=True
            )

        if destino.guild.id != interaction.guild.id:
            return await interaction.response.send_message(
                "O canal precisa pertencer a este servidor.",
                ephemeral=True
            )

        permissoes = destino.permissions_for(interaction.guild.me)

        if not permissoes.send_messages or not permissoes.embed_links:
            return await interaction.response.send_message(
                "Não tenho permissão para enviar mensagens e embeds nesse canal.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📨 Confissão anônima",
            description=mensagem,
            color=discord.Color.dark_purple()
        )

        embed.set_footer(text="DROPZIN • Caixa de confissões")

        try:
            await destino.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )

            await interaction.response.send_message(
                f"✅ Sua confissão foi publicada em {destino.mention}.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Não tenho permissão para publicar nesse canal.",
                ephemeral=True
            )

        except discord.HTTPException:
            await interaction.response.send_message(
                "Não consegui publicar a confissão. Tente novamente.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Confissao(bot))
