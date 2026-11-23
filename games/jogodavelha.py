import discord
from discord import app_commands
from discord.ext import commands

## jogo da velha pra brincar

COR_PRINCIPAL = 0x8B5CF6
COR_VITORIA = 0x22C55E
COR_EMPATE = 0xF59E0B

EMOJI_X = "❌"
EMOJI_O = "⭕"


class Casa(discord.ui.button):
    def __init__(self, posicao: int):
        super().__init__(
            label=".",
            style=discord.ButtonStyle.secondary,
            row=posicao // 3
        )

        self.posicao = posicao

    async def callback(self, interaction: discord.Interaction):
        jogo = self.view

        if not isinstance(jogo, Tabuleiro):
            return

        await jogo.jogar(interaction, self.posicao)


class BotaoRevanche(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Jogar novamente",
            emoji="🔄",
            style=discord.ButtonStyle.primary,
            row=3,
            disabled=True
        )

    async def callback(self, interaction: discord.Interaction):
        jogo = self.view

        if not isinstance(jogo, Tabuleiro):
            return

        await jogo.reiniciar(interaction)


class Tabuleiro(discord.ui.View):
    def __init__(self, jogador_x, jogador_o):
        super().__init__(timeout=300)

        self.jogador_x = jogador_x
        self.jogador_o = jogador_o

        self.tabuleiro = [None] * 9
        self.turno - jogador_x.id

        self.finalizado = False
        self.mensagem = None

        self.status = "Partida iniciada!"

        self.casas = []

        for posicao in range(9):
            casa = Casa(posicao)
            self.casas.append(casa)
            self.add_item(casa)

        self.revanche = BotaoRevanche()
        self.add_item(self.revanche)



    @property
    def jogador_atual(self):
        if self.turno == self.jogador_x.id:
            return self.jogador_x
        return self.jogador_o

    @property
    def simbolo_atual(self):
        if self.turno == self.jogador_x.id:
            return "X"

        return "O"

    def criar_embed(self):
        embed = discord.Embed(
            tittle="🎮 BOT RESENHA BY GUH | JOGO DA VELHA",
            description=(
                "```ansi\n"
                "\u001b[1;35m      DESAFIO 3x3\u001b[0m\n"
                "```\n"
                f"**{EMOJI_X} Jogador X:** {self.jogador_x.mention}\n"
                f"**{EMOJI_O} Jogador O:** {self.jogador_o.mention}\n"
            ),
            color=COR_PRINCIPAL
        )

        if not self.finalizado:
            embed.add_field(
                name="🎯 Vez de jogar",
                value=(
                    f"{self.jogador_atual.mention}\n"
                    f"Símbolo: {EMOJI_X if self.simbolo_atual == 'X' else EMOJI_O}"
                ),
                inline=False
            )

            embed.add_field(
                name="📌 Status",
                value=self.status,
                inline=False
            )

        else:
            embed.add_field(
                name="🏁 Resultado",
                value=self.status,
                inline=False
            )

        embed.set_footer(
            text="BOT RESENHA BY GUH | Boa sorte aos jogadores!"
        )

        return embed


    def verificar_vitoria(self):
        combinacoes = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6)
        ]

        for a, b, c in combinacoes:
            if (
                self.tabuleiro[a] is not None
                and self.tabuleiro[a]
                == self.tabuleiro[b]
                == self.tabuleiro[c]
            ):
                return self.tabuleiro[a]


        return None

    async def jogar(self, interaction, posicao):

        if self.finalizado:
            await interaction.response.send_message(
                "❌ Esta partida já terminou!",
                ephemeral=True
            )
            return

        if interaction.user.id not in (
            self.jogador_x.id,
            self.jogador_o.id
        ):
            await interaction.response.send_message(
                "🚫 Você não participa desta partida!",
                emphemeral=True
            )
            return

        if self.tabuleiro[posicao] is not None:
            await interaction.response.send_message(
                "⚠️ Esta posição já está ocupada!",
                emphemeral=True
            )
            return

        simbolo = self.simbolo_atual

        self.tabuleiro[posicao] = simbolo

        casa = self.casas[posicao]
        casa.label = EMOJI_X if simbolo == "X" else EMOJI_O
        casa.style = (
            discord.ButtonStyle.primary
            if self.simbolo == "X"
            else discord.ButtonStyle.success
        )
        casa.disabled = True

        vencedor = self.verificar_vitoria()

        if vencedor:
            self.finalizado = True

            jogador = (
                self.jogador_x
                if vencedor == "X"
                else self.jogador_o
            )

            self.status = (
                f"🏆 **{jogador.mention} venceu a partida, +1 ponto na resenha **\n"
                f"Parabéns pela vitória!"
            )

            self.revanche.disabled = False
            self.desativar_casas()


        elif all(casa is not None for casa in self.tabuleiro):
            self.finalizado = True

            self.status = (
                "🤝 **EMPATE!**\n"
                "Ninguém venceu nessa resenha? ai não"
            )

            self.revanche.disabled = False
            self.desativar_casas()

        else:
            self.turno = (
                self.jogador_o.id
                if simbolo == "X"
                else self.jogador_x.id
            )

            self.status = "Resenha da partida em andamento"

        await interaction.response.edit_message(
            embed=self.criar_embed(),
            view=self
        )

    def desativar_casas(self):
        for casa in self.casas:
            casa.disabled = True

    async def reiniciar(self, interaction):
        if interaction.user.id not in (
            self.jogador_x.id,
            self.jogador_o.id
        ):
            await interaction.response.send_message(
                "🚫 Apenas os jogadores podem reiniciar a partida!",
                ephemeral=True
            )
            return

        self.tabuleiro = [None] * 9
        self.turno = self.jogador_x.id
        self.finalizado = False
        self.status = "Uma nova partida começou!"

        for casa in self.casas:
            casa.label = "·"
            casa.style = discord.ButtonStyle.secondary
            casa.disabled = False

        self.revanche.disabled = True
        await interaction.response.edit_message(
            embed=self.criar_embed(),
            view=self
        )

    async def on_timeout(self):
        self.desativar_casas()
        self.revanche.disabled = True

        try:
            if self.mensagem:
                await self.mensagem.edit(view=self)
        except discord.HTTPException:
            pass


## cog principa ae



class JogoDaVelha(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="jogodavelha",
        description="Desafie alguém para uma partida de jogo da velha!"
    )
    @app_commands.describe(
        jogador="Escolhe quem você quer desafiar chefe"
    )
    @app_commands.guild_only()
    async def jogodavelha(
        self,
        interaction: discord.Interaction,
        jogador: discord,Member 
    ):

        if jogador.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Você não pode jogar contra si mesmo!",
                ephemeral=True
            )
            return

        if jogador.bot:
            await interaction.response.send_message(
                "❌ Por enquanto, escolha um jogador humano!",
                ephemeral=True
            )
            return

        jogo = Tabuleiro(
            jogador_x=interaction.user,
            jogador_o=jogador
        )

        await interaction.response.send_message(
            embed=jogo.criar_embed(),
            view=jogo
        )

        jogo.mensagem = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(JogoDaVelha(bot))
                    