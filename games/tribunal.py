import discord
import random

from discord.ext import commands
from discord import app_commands

class JulgamentoView(discord.ui.View):

    def __init__(self, juiz, acusado, denunciante, motivo):
        super().__init__(timeout=300)

        self.juiz = juiz
        self.acusado = acusado
        self.denunciante = denunciante
        self.motivo = motivo
        self.pena = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.juiz.id:
            await interaction.response.send_message(
                "⚖️ Somente o juiz sorteado pode decidir este processo.",
                ephemeral=True
            )
            return False
        
        return True

    @discord.ui.select(
        placeholder="Escolha a pena fictícia...",
        options=[
            discord.SelectOption(
                label="Pagar uma coxinha",
                value="Pagar uma coxinha"
            ),
            discord.SelectOption(
                label="Quitar qualquer divida que tem com o safado",
                value="Quitar qualquer divida que tem com o safado"
            ),
            discord.SelectOption(
                label="Usar um nickname engraçado por 15 minutos",
                value="Usar um nickname engraçado por 15 minutos"
            ),
            discord.SelectOption(
                label="Enviar mensagem para ex pedindo para voltar",
                value="Enviar mensagem para ex pedindo para voltar"
            ),
            discord.SelectOption(
                label="Mamar o ADM do bot",
                value="Mamar o ADM do bot"
            ),
            discord.SelectOption(
                label="Fazer qualquer que o Dono do server mandar",
                value="Fazer qualquer que o Dono do server mandar"
            ),
            discord.SelectOption(
                label="Fazer qualquer coisa que o Dono do bot mandar",
                value="Fazer qualquer coisa que o Dono do bot mandar"
            ),
            discord.SelectOption(
                label="Confressar para a pessoa que você gosta que você gosta dela",
                value="Confressar para a pessoa que você gosta que você gosta dela"
            ),
            discord.SelectOption(
                label="Nenhuma pena",
                value="Nenhuma pena"
            )
        ]
    )

    async def selecionar_pena(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):
        self.pena = select.values[0]

        await interaction.response.send_message(
            f"Pena selecionada: **{self.pena}**",
            ephemeral=True
        )

    async def finalizar(self, interaction, culpado):

        if self.pena is None:
            return await interaction.response.send_message(
                "Escolha uma pena antes de apresentar o veredito.",
                ephemeral=True
            )

        resultado = "CULPADO" if culpado else "INOCENTE"

        embed = discord.Embed(
            title="⚖️ Tribunal do DROPZIN",
            description=(
                f"**Denunciante:** {self.denunciante.mention}\n"
                f"**Acusado:** {self.acusado.mention}\n"
                f"**Juiz:** {self.juiz.mention}\n\n"
                f"**Motivo:** {self.motivo}\n\n"
                f"**Veredito:** {resultado}\n"
                f"**Pena:** {self.pena if culpado else 'Nenhuma'}"
            ),
            color=(
                discord.Color.red()
                if culpado
                else discord.Color.green()
            )
        )

        embed.set_footer(text="Processo encerrado pelo Tribunal do DROPZIN.")

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        self.stop()

    @discord.ui.button(
        label="Culpado",
        style=discord.ButtonStyle.danger,
        emoji="🔨"
    )
    async def culpado(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.finalizar(interaction, True)

    @discord.ui.button(
        label="Inocente",
        style=discord.ButtonStyle.success,
        emoji="⚖️"
    )
    async def inocente(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.finalizar(interaction, False)


class Tribunal(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="tribunal",
        description="Abra um processo contra alguém do servidor."
    )
    @app_commands.describe(
        usuario="Pessoa que será julgada",
        motivo="Motivo da denúncia"
    )
    async def tribunal(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: str
    ):

        guild = interaction.guild

        if guild is None:
            return await interaction.response.send_message(
                "Este comando só funciona dentro de um servidor.",
                ephemeral=True
            )

        if usuario.bot:
            return await interaction.response.send_message(
                "Você não pode abrir um processo contra um bot.",
                ephemeral=True
            )

        if usuario.id == interaction.user.id:
            return await interaction.response.send_message(
                "Você não pode abrir um processo contra si mesmo.",
                ephemeral=True
            )

        membros_online = [
            membro
            for membro in guild.members
            if not membro.bot
            and membro.id not in (
                usuario.id,
                interaction.user.id
            )
            and membro.status != discord.Status.offline
        ]

        if not membros_online:
            return await interaction.response.send_message(
                "Não encontrei um juiz disponível. "
                "Verifique as permissões de membros e presença do bot.",
                ephemeral=True
            )

        juiz = random.choice(membros_online)

        embed = discord.Embed(
            title="⚖️ Novo processo aberto!",
            description=(
                f"**Denunciante:** {interaction.user.mention}\n"
                f"**Acusado:** {usuario.mention}\n"
                f"**Juiz sorteado:** {juiz.mention}\n\n"
                f"**Motivo da denúncia:**\n{motivo}\n\n"
                "O juiz deve escolher uma pena e apresentar o veredito."
            ),
            color=discord.Color.gold()
        )

        embed.set_footer(text="Tribunal do DROPZIN")

        view = JulgamentoView(
            juiz,
            usuario,
            interaction.user,
            motivo
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )


async def setup(bot):
    await bot.add_cog(Tribunal(bot))
