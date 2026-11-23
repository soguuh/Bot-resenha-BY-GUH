
import random
import unicodedata

from pathlib import Path
from discord.ext import commands


# Localiza palavras_pt.txt na raiz do projeto
ARQUIVO_PALAVRAS = (
    Path(__file__).resolve().parent.parent / "palavras_pt.txt"
)


def normalizar_palavra(palavra):
    return "".join(
        letra
        for letra in unicodedata.normalize("NFD", palavra.lower())
        if unicodedata.category(letra) != "Mn"
    )


def obter_palavra_forca():

    if not ARQUIVO_PALAVRAS.exists():
        raise FileNotFoundError(
            "O arquivo palavras_pt.txt não foi encontrado."
        )

    with ARQUIVO_PALAVRAS.open(
        "r",
        encoding="utf-8"
    ) as arquivo:

        palavras = [
            normalizar_palavra(linha.strip())
            for linha in arquivo
            if linha.strip()
        ]

    palavras_validas = [
        palavra
        for palavra in palavras
        if palavra.isalpha() and 4 <= len(palavra) <= 15
    ]

    if not palavras_validas:
        raise ValueError(
            "Não existem palavras válidas no arquivo."
        )

    return random.choice(palavras_validas)


class Forca(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partidas = {}

    @commands.command(name="forca")
    async def forca(self, ctx, letra: str = None):

        usuario = str(ctx.author.id)

        # Iniciar partida
        if letra is None:

            try:
                palavra = obter_palavra_forca()

            except (FileNotFoundError, ValueError) as erro:
                print(f"Erro ao iniciar a forca: {erro}")

                await ctx.send(
                    f"Não foi possível iniciar jogo: {erro}"
                )
                return

            self.partidas[usuario] = {
                "palavra": palavra,
                "letras": [],
                "erros": 0
            }

            await ctx.send(
                "🔤 **JOGO DA FORCA INICIADO!**\n"
                "Adivinhe a palavra usando `/forca letra`."
            )
            return

        jogo = self.partidas.get(usuario)

        if not jogo:
            await ctx.send(
                "Não existe partida ativa. Digite `/forca` para começar."
            )
            return

        letra = normalizar_palavra(letra.strip())

        if len(letra) != 1 or not letra.isalpha():
            await ctx.send("Digite somente uma letra.")
            return

        if letra in jogo["letras"]:
            await ctx.send("Você já tentou essa letra!")
            return

        jogo["letras"].append(letra)

        if letra not in jogo["palavra"]:
            jogo["erros"] += 1

        palavra = jogo["palavra"]

        exibicao = " ".join(
            l if l in jogo["letras"] else "_"
            for l in palavra
        )

        # Vitória
        if all(l in jogo["letras"] for l in palavra):

            del self.partidas[usuario]

            self.bot.adicionar_xp(ctx.author.id, 25)

            await ctx.send(
                f"🏆 **VOCÊ VENCEU!**\n"
                f"A palavra era: **{palavra}**\n"
                "⭐ +25 XP"
            )

        # Derrota
        elif jogo["erros"] >= 6:

            del self.partidas[usuario]

            await ctx.send(
                f"❌ **FIM DE JOGO!**\n"
                f"A palavra era: **{palavra}**\n"
                "Digite `/forca` para começar outra partida."
            )

        # Partida continua
        else:

            await ctx.send(
                f"🔤 **JOGO DA FORCA**\n"
                f"Palavra: `{exibicao}`\n"
                f"Letras tentadas: {', '.join(jogo['letras'])}\n"
                f"Erros: {jogo['erros']}/6"
            )


async def setup(bot):
    await bot.add_cog(Forca(bot))
