
import random
from discord.ext import commands


class Adivinhar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partidas = {}

    @commands.command(name="adivinhar")
    async def adivinhar(self, ctx, tentativa: int = None):
        usuario = str(ctx.author.id)

        if tentativa is None:
            self.partidas[usuario] = random.randint(1, 100)

            await ctx.send(
                "🎯 Pensei em um número entre 1 e 100!\n"
                "Use `/adivinhar número` para tentar."
            )
            return

        if not 1 <= tentativa <= 100:
            await ctx.send(
                "Digite um número inteiro entre 1 e 100."
            )
            return

        if usuario not in self.partidas:
            await ctx.send(
                "Primeiro inicie o jogo com `/adivinhar`."
            )
            return

        numero = self.partidas[usuario]

        if tentativa == numero:
            del self.partidas[usuario]

            self.bot.adicionar_xp(ctx.author.id, 25)

            await ctx.send(
                "🏆 **Você acertou!**\n"
                "⭐ Você ganhou 25 XP!"
            )

        elif tentativa < numero:
            await ctx.send("📈 Meu número é maior!")

        else:
            await ctx.send("📉 Meu número é menor!")


async def setup(bot):
    await bot.add_cog(Adivinhar(bot))
