import asyncio
import json
import random
from pathlib import Path

import discord
from discord.ext import commands

DATA_DIR = Path(__file__).resolve().parent / "dados"
QUESTIONS_FILE = DATA_DIR / "perguntas.json"
STATS_FILE = DATA_DIR / "estatisticas_quiz.json"
MATERIAS_DIR = DATA_DIR / "materias"


MATERIAS_ARQUIVOS = {
    "informatica": "Informática",
    "matematica": "Matemática",
    "ciencias": "Ciências",
    "historia": "História",
    "geografia": "Geografia",
    "conhecimento_geral": "Conhecimento Geral",
    "logica": "Lógica",
    "literatura": "Literatura",
    "astronomia": "Astronomia",
    "portugues": "Português",
    "ingles": "Inglês",
    "fisica": "Física",
    "quimica": "Química",
    "biologia": "Biologia",
    "filosofia": "Filosofia",
    "sociologia": "Sociologia",
    "arquitetura_computadores": "Arquitetura Física e Lógica de Computadores",
    "programacao": "Programação",
    "engenharia_software": "Engenharia de Software",
    "engenharia_reversa": "Engenharia Reversa",
    "engenharia_social": "Engenharia Social",
    "ciberseguranca": "Cibersegurança",
    "republica": "República",
    "acontecimentos_historicos": "Acontecimentos Históricos",
    "fatos_historicos": "Fatos Históricos",
    "artes_artistas": "Artes e Artistas",
    "obras": "Obras",
    "administracao": "Administração",
    "ciencia_computacao": "Ciência da Computação",
    "engenharia_computacao": "Engenharia da Computação",
    "engenharia_mecanica": "Engenharia Mecânica",
    "engenharia_civil": "Engenharia Civil",
    "psicologia": "Psicologia"
}



def carregar_json(caminho, padrao):
    try:
        with caminho.open("r", encoding="utf-8-sig") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")

    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

    temporario.replace(caminho)

def carregar_todas_perguntas():
    perguntas = []
    identificadores = set()

    arquivos = [(QUESTIONS_FILE, None)]

    for arquivo in MATERIAS_DIR.glob("*.json"):
        nome_arquivo = arquivo.stem.lower()
        materia = MATERIAS_ARQUIVOS.get(nome_arquivo)

        if materia:
            arquivos.append((arquivo, materia))

    for caminho, materia_arquivo in arquivos:
        dados = carregar_json(caminho, [])

        if not isinstance(dados, list):
            print(f"[QUIZ] Arquivo Ignorado: {caminho.name}")
            continue
        for pergunta in dados:
            if not isinstance(pergunta, dict):
                continue
            if materia_arquivo:
                pergunta["materia"] = materia_arquivo

            campos = ["materia", "assunto", "perguntas", "opcoes", "resposta"]

            if not all(campo in pergunta for campo in campos):
                continue
            if not isinstance(pergunta["opcoes"], list) or len(pergunta["opcoes"]) != 4:
                continue

            resposta = str(pergunta["resposta"]).upper().strip()

            if resposta not in ("A", "B", "C", "D"):
                continue

            pergunta["resposta"] = resposta

            identificador = (
                str(pergunta["materia"]).strip().lower(),
                str(pergunta["assunto"]).strip().lower(),
                str(pergunta["pergunta"]).strip().lower(),
            )

            if identificador in identificadores:
                continue
            identificadores.add(identificador)
            perguntas.append(pergunta)

        print(f"[QUIZ] Total de perguntas carregadas: {len(perguntas)}")
        print(f"[QUIZ] Matérias encontradas: {len(set(p["materia"] for p in perguntas))}")
        return perguntas


class SelecaoMateria(discord.ui.Select):
    def __init__(self, cog, canal_id, materias, pagina=0):
        self.cog = cog
        self.canal_id = canal_id

        inicio = pagina * 25
        materias_pagina = materias[inicio:inicio + 25]

        opcoes = [
            discord.SelectOption(label=materia[:100], value=materia)
            for materia in materias_pagina
        ]

        super().__init__(
            placeholder=f"Escolha a matéria — página {pagina + 1}",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction: discord.Interaction):
        partida = self.cog.partidas.get(self.canal_id)

        if not partida or interaction.user.id != partida["organizador"]:
            return await interaction.response.send_message(
                "Somente quem iniciou o quiz pode escolher a matéria.",
                ephemeral=True
            )

        materia = self.values[0]
        partida["materia"] = materia

        assuntos = sorted({
            p["assunto"]
            for p in partida["perguntas"]
            if p["materia"] == materia
        })

        if not assuntos:
            return await interaction.response.send_message(
                "Não há perguntas cadastradas nessa matéria ainda.",
                ephemeral=True
            )

        view = SelecaoAssuntoView(self.cog, self.canal_id, assuntos)

        await interaction.response.edit_message(
            content=f"**Matéria escolhida:** {materia}\nAgora escolha o assunto:",
            view=view
        )



class SelecaoAssunto(discord.ui.Select):
    def __init__(self, cog, canal_id, assuntos):
        self.cog = cog
        self.canal_id = canal_id
        opcoes = [
            discord.SelectOption(label=assunto[:100], value=assunto)
            for assunto in assuntos[:25]
        ]
        super().__init__(
            placeholder="Escolha o assunto...",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction: discord.Interaction):
        partida = self.cog.partidas.get(self.canal_id)
        if not partida or interaction.user.id != partida["organizador"]:
            return await interaction.response.send_message(
                "Somente quem iniciou o quiz pode escolher o assunto.",
                ephemeral=True
            )

        assunto = self.values[0]
        partida["assunto"] = assunto
        partida["fila"] = [
            p for p in partida["perguntas"]
            if p["materia"] == partida["materia"]
            and p["assunto"] == assunto
        ]

        random.shuffle(partida["fila"])

        quantidade_solicitada = partida["quantidade"]
        quantidade_disponivel = len(partida["fila"])

        partida["fila"] = partida["fila"][:quantidade_solicitada]

        if not partida["fila"]:
            return await interaction.response.send_message(
                "Não existem perguntas cadastradas nesse assunto.",
                ephemeral=True
            )
        
        partida["pontos"] = {uid: 0 for uid in partida["jogadores"]}
        partida["respondidos"] = set()
        partida["numero"] = 0

        await interaction.response.edit_message(
            content=(
                f"**Quiz iniciado!**\nMatéria: **{partida['materia']}**\n"
                f"Assunto: **{assunto}**\n"
                f"Participantes: **{len(partida['jogadores'])}**\n"
                "Cada pergunta terá 25 segundos."
            ),
            view=None
        )
        await self.cog.proxima_pergunta(self.canal_id)

class SelecaoAssuntoView(discord.ui.View):
    def __init__(self, cog, canal_id, assuntos):
        super().__init__(timeout=180)
        self.add_item(SelecaoAssunto(cog, canal_id, assuntos))

class SelecaoQuantidade(discord.ui.Select):
    def __init__(self, cog, canal_id):
        self.cog = cog
        self.canal_id = canal_id

        opcoes = [
            discord.SelectOption(
                label=f"{n} perguntas",
                value=str(n)
            )
            for n in [5, 10, 20, 30, 40, 50, 100]
        ]

        super().__init__(
            placeholder="Escolha a quantidade de rodadas...",
            min_values=1,
            max_values=1,
            options=opcoes
        )

    async def callback(self, interaction: discord.Interaction):
        partida = self.cog.partidas.get(self.canal_id)

        if not partida:
            return await interaction.response.send_message(
                "Essa configuração expirou.",
                ephemeral=True
            )
        if interaction.user.id != partida["organizador"]:
            return await interaction.response.send_message(
                "Somentequem iniciou o quiz pode configurar partida.",
                ephemeral=True
            )

        partida["quantidade"] = int(self.values[0])

        view = SelecaoMateriaView(
            self.cog,
            self.canal_id,
            partida["materias"]
        )

        await interaction.response.edit_message(
            content=(
                f"**Quantidade escolhida: {partida['quantidade']} perguntas.**\n"
                "Agora escolha a matéria:"
            ),
            view=view
        )

class SelecaoQuantidadeView(discord.ui.View):
    def __init__(self, cog, canal_id):
        super().__init__(timeout=180)
        self.add_item(SelecaoQuantidade(cog, canal_id))


class SelecaoMateriaView(discord.ui.View):
    def __init__(self, cog, canal_id, materias, pagina=0):
        super().__init__(timeout=180)

        self.cog = cog
        self.canal_id = canal_id
        self.materias = materias
        self.pagina = pagina

        self.add_item(SelecaoMateria(cog, canal_id, materias, pagina))

        total_paginas = (len(materias) + 24) // 25

        if pagina > 0:
            self.add_item(BotaoPaginaMateria(-1))

        if pagina < total_paginas - 1:
            self.add_item(BotaoPaginaMateria(1))


class BotaoPaginaMateria(discord.ui.Button):
    def __init__(self, direcao):
        self.direcao = direcao

        texto = "Página anterior" if direcao == -1 else "Próxima página"

        super().__init__(
            label=texto,
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        view_atual = self.view

        partida = view_atual.cog.partidas.get(view_atual.canal_id)

        if not partida or interaction.user.id != partida["organizador"]:
            return await interaction.response.send_message(
                "Somente quem iniciou o quiz pode navegar.",
                ephemeral=True
            )

        nova_pagina = view_atual.pagina + self.direcao

        nova_view = SelecaoMateriaView(
            view_atual.cog,
            view_atual.canal_id,
            view_atual.materias,
            nova_pagina
        )

        await interaction.response.edit_message(view=nova_view)


class SelecaoView(discord.ui.View):
    def __init__(self, cog, canal_id, materias):
        super().__init__(timeout=180)
        self.add_item(SelecaoMateria(cog, canal_id, materias))


class RespostaButton(discord.ui.Button):
    def __init__(self, cog, canal_id, indice, texto):
        super().__init__(
            label=f"{chr(65 + indice)} — {texto[:70]}",
            style=discord.ButtonStyle.primary,
            custom_id=f"quiz_{canal_id}_{indice}"
        )
        self.cog = cog
        self.canal_id = canal_id
        self.indice = indice

    async def callback(self, interaction: discord.Interaction):
        partida = self.cog.partidas.get(self.canal_id)
        if not partida:
            return await interaction.response.send_message(
                "Essa rodada já terminou.", ephemeral=True
            )

        uid = interaction.user.id
        if uid not in partida["jogadores"]:
            return await interaction.response.send_message(
                "Você não estava na call quando o quiz começou.",
                ephemeral=True
            )

        if uid in partida["respondidos"]:
            return await interaction.response.send_message(
                "Você já respondeu esta pergunta.", ephemeral=True
            )

        pergunta = partida["pergunta_atual"]
        partida["respondidos"].add(uid)
        correta = pergunta["resposta"].upper() == chr(65 + self.indice)
        if correta:
            partida["pontos"][uid] += 10

        await interaction.response.send_message(
            "Resposta registrada! " + ("Você acertou." if correta else "Resposta registrada."),
            ephemeral=True
        )

        await self.cog.atualizar_contador(self.canal_id)
        if len(partida["respondidos"]) >= len(partida["jogadores"]):
            await self.cog.finalizar_rodada(self.canal_id, motivo="Todos responderam.")


class RespostasView(discord.ui.View):
    def __init__(self, cog, canal_id, opcoes):
        super().__init__(timeout=None)
        for indice, texto in enumerate(opcoes):
            self.add_item(RespostaButton(cog, canal_id, indice, texto))


class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partidas = {}
        self.stats = carregar_json(STATS_FILE, {"usuarios": {}})

    def salvar_stats(self):
        salvar_json(STATS_FILE, self.stats)

    def pegar_jogadores_da_call(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return None, "Entre em uma call de voz antes de iniciar o quiz."

        canal_voz = ctx.author.voice.channel
        jogadores = {
            membro.id: membro
            for membro in canal_voz.members
            if not membro.bot
        }
        if len(jogadores) < 1:
            return None, "Não encontrei participantes na call."
        return jogadores, None

    @commands.command(name="quiz")
    async def quiz(self, ctx):
        """Inicia um quiz para as pessoas que estão na mesma call de voz."""
        if ctx.channel.id in self.partidas:
            return await ctx.send("Já existe um quiz ativo neste canal de texto.")

        jogadores, erro = self.pegar_jogadores_da_call(ctx)
        if erro:
            return await ctx.send(erro)

        perguntas = carregar_todas_perguntas()
        materias = sorted({
            p.get("materia")
            for p in perguntas
            if p.get("materia")
        })
        if not materias:
            return await ctx.send("O banco de perguntas está vazio. Confira games/dados/perguntas.json.")

        self.partidas[ctx.channel.id] = {
            "materias": materias,
            "quantidade": 10,
            "organizador": ctx.author.id,
            "jogadores": jogadores,
            "perguntas": perguntas,
            "materia": None,
            "assunto": None,
            "fila": [],
            "numero": 0,
            "pontos": {},
            "respondidos": set(),
            "pergunta_atual": None,
            "mensagem": None,
            "view": None,
            "timer": None,
            "finalizando": False,
            "canal_voz_id": ctx.author.voice.channel.id
        }

        view = SelecaoQuantidadeView(self, ctx.channel.id)
        await ctx.send(
            f"**GUH QUIZ — seleção de matéria**\n"
            f"Encontrei **{len(jogadores)} jogador(es)** na call "
            f"**{ctx.author.voice.channel.name}**.\n"
            "Quem iniciou o quiz escolhe a matéria e o assunto abaixo.",
            view=view
        )

    async def proxima_pergunta(self, canal_id):
        partida = self.partidas.get(canal_id)
        if not partida:
            return

        if partida["numero"] >= len(partida["fila"]):
            return await self.encerrar_quiz(canal_id, "As perguntas cadastradas acabaram.")

        pergunta = partida["fila"][partida["numero"]]
        partida["numero"] += 1
        partida["pergunta_atual"] = pergunta
        partida["respondidos"] = set()
        partida["finalizando"] = False

        canal = self.bot.get_channel(canal_id)
        if canal is None:
            self.partidas.pop(canal_id, None)
            return

        embed = discord.Embed(
            title=f"GUH QUIZ — Pergunta {partida['numero']}/{len(partida['fila'])}",
            description=pergunta["pergunta"],
            color=discord.Color.blurple()
        )
        embed.add_field(name="Matéria", value=partida["materia"], inline=True)
        embed.add_field(name="Assunto", value=partida["assunto"], inline=True)
        embed.add_field(name="Tempo", value="25 segundos", inline=True)
        embed.set_footer(text="Responda individualmente pelos botões. Cada jogador tem uma tentativa.")

        view = RespostasView(self, canal_id, pergunta["opcoes"])
        mensagem = await canal.send(embed=embed, view=view)
        partida["view"] = view
        partida["mensagem"] = mensagem
        partida["timer"] = asyncio.create_task(self.cronometro(canal_id, mensagem.id))

    async def cronometro(self, canal_id, mensagem_id):
        try:
            await asyncio.sleep(25)
            partida = self.partidas.get(canal_id)
            if partida and partida["mensagem"] and partida["mensagem"].id == mensagem_id:
                await self.finalizar_rodada(canal_id, motivo="O tempo de 25 segundos acabou.")
        except asyncio.CancelledError:
            pass

    async def atualizar_contador(self, canal_id):
        partida = self.partidas.get(canal_id)

        if not partida or not partida["mensagem"]:
            return

        try:
            mensagem = partida["mensagem"]
            embed = mensagem.embeds[0] if mensagem.embeds else None

            if embed:
                embed.set_field_at(
                    2,
                    name="Respostas",
                    value=(
                        f"{len(partida['respondidos'])}/"
                        f"{len(partida['jogadores'])}"
                    ),
                    inline=True
                )

                await mensagem.edit(
                    embed=embed,
                    view=partida.get("view")
                )
        except discord.HTTPException as erro:
            print(f"[QUIZ] Erro ao atualizar contador: {erro}")

    async def finalizar_rodada(self, canal_id, motivo):
        partida = self.partidas.get(canal_id)
        if not partida or partida["finalizando"]:
            return
        partida["finalizando"] = True

        timer = partida.get("timer")
        if timer and timer is not asyncio.current_task():
            timer.cancel()

        pergunta = partida["pergunta_atual"]
        letra = pergunta["resposta"].upper()
        if partida.get("mensagem"):
            try:
                await partida["mensagem"].edit(view=None)
            except discord.HTTPException:
                pass
        canal = self.bot.get_channel(canal_id)
        if canal:
            await canal.send(
                f"⏱️ **Rodada encerrada!** {motivo}\n"
                f"Resposta correta: **{letra} — {pergunta['opcoes'][ord(letra) - 65]}**"
            )
            await asyncio.sleep(2)
            await self.proxima_pergunta(canal_id)

    @commands.command(name="final_quiz")
    async def final_quiz(self, ctx):
        """Encerra imediatamente a pergunta atual e avança."""
        partida = self.partidas.get(ctx.channel.id)
        if not partida:
            return await ctx.send("Não existe um quiz ativo neste canal.")
        if ctx.author.id not in partida["jogadores"]:
            return await ctx.send("Só participantes da call podem encerrar a rodada.")
        await self.finalizar_rodada(ctx.channel.id, f"{ctx.author.mention} encerrou a rodada.")

    async def encerrar_quiz(self, canal_id, motivo):
        partida = self.partidas.pop(canal_id, None)
        if not partida:
            return

        timer = partida.get("timer")
        if timer:
            timer.cancel()

        jogadores = partida["jogadores"]
        pontos = partida["pontos"]
        ranking = sorted(pontos.items(), key=lambda item: item[1], reverse=True)

        linhas = []
        for posicao, (uid, total) in enumerate(ranking, start=1):
            membro = jogadores.get(uid)
            nome = membro.display_name if membro else f"Usuário {uid}"
            linhas.append(f"**{posicao}º** {nome}: **{total} pontos**")

            registro = self.stats["usuarios"].setdefault(str(uid), {
                "partidas": 0, "pontos": 0, "vitorias": 0
            })
            registro["partidas"] += 1
            registro["pontos"] += total
            if posicao == 1 and total > 0:
                registro["vitorias"] += 1
            if hasattr(self.bot, "adicionar_xp") and total > 0:
                self.bot.adicionar_xp(uid, max(5, total // 2))

        self.salvar_stats()
        canal = self.bot.get_channel(canal_id)
        if canal:
            embed = discord.Embed(
                title="🏆 Resultado final do GUH QUIZ",
                description=motivo + "\n\n" + ("\n".join(linhas) if linhas else "Sem pontuação."),
                color=discord.Color.gold()
            )
            await canal.send(embed=embed)

    @commands.command(name="ranking_quiz")
    async def ranking_quiz(self, ctx):
        ranking = sorted(
            self.stats["usuarios"].items(),
            key=lambda item: item[1].get("pontos", 0),
            reverse=True
        )[:10]
        if not ranking:
            return await ctx.send("Ainda não há estatísticas do quiz.")
        linhas = []
        for posicao, (uid, dados) in enumerate(ranking, start=1):
            linhas.append(
                f"**{posicao}º** <@{uid}> — {dados.get('pontos', 0)} pontos "
                f"({dados.get('partidas', 0)} partidas)"
            )
        await ctx.send("**RANKING GUH QUIZ**\n" + "\n".join(linhas))


async def setup(bot):
    await bot.add_cog(Quiz(bot))
