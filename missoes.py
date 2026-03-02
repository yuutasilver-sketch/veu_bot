import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
from datetime import datetime, timedelta

from database import load_json, save_json, ensure_user
import config


class Missoes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_times = {}

    # ================= VIEW BOTÃO =================

    class ResgatarView(discord.ui.View):
        def __init__(self, user_id):
            super().__init__(timeout=120)
            self.user_id = user_id

        @discord.ui.button(label="🎁 Resgatar recompensas", style=discord.ButtonStyle.green)
        async def resgatar_button(self, interaction: discord.Interaction, button: discord.ui.Button):

            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "Você não pode resgatar as missões de outra pessoa.",
                    ephemeral=True
                )
                return

            missoes = load_json(config.MISSOES_FILE, {})
            users = load_json(config.USERS_DB, {})

            if not isinstance(missoes, dict):
                missoes = {}
            if not isinstance(users, dict):
                users = {}

            uid = str(interaction.user.id)

            if uid not in missoes:
                await interaction.response.send_message(
                    "Você não tem missões.",
                    ephemeral=True
                )
                return

            total = 0
            for nome in ["mensagens", "evento", "evento_raro", "fragmentos", "call", "semanal"]:
                m = missoes[uid].get(nome)
                if m and m.get("concluida") and not m.get("resgatada", False):
                    total += m.get("recompensa", 0)
                    m["resgatada"] = True

            if total == 0:
                await interaction.response.send_message(
                    "Nada para resgatar.",
                    ephemeral=True
                )
                return

            ensure_user(users, interaction.user.id)
            users.setdefault(uid, {})
            users[uid].setdefault("fragmentos", 0)
            users[uid]["fragmentos"] += total

            save_json(config.USERS_DB, users)
            save_json(config.MISSOES_FILE, missoes)

            await interaction.response.send_message(
                f"🎉 Você ganhou **{total} Fragmentos!**",
                ephemeral=True
            )

    # ================= START LOOP =================

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.reset_missoes.is_running():
            self.reset_missoes.start()

    def cog_unload(self):
        if self.reset_missoes.is_running():
            self.reset_missoes.cancel()

    # ================= GERAR MISSÕES =================

    def gerar_missoes(self):
        return {
            "nivel": 1,
            "mensagens": {"meta": random.randint(15, 30), "progresso": 0, "recompensa": random.randint(200, 500), "concluida": False},
            "evento": {"meta": 1, "progresso": 0, "recompensa": random.randint(400, 800), "concluida": False},
            "evento_raro": {"meta": 1, "progresso": 0, "recompensa": 1500, "concluida": False},
            "fragmentos": {"meta": random.randint(1000, 3000), "progresso": 0, "recompensa": random.randint(500, 900), "concluida": False},
            "call": {"meta": random.randint(10, 30), "progresso": 0, "recompensa": random.randint(400, 800), "concluida": False},
            "semanal": {"meta": random.randint(3, 7), "progresso": 0, "recompensa": 3000, "concluida": False},
            "reset": (datetime.utcnow() + timedelta(hours=24)).timestamp(),
            "reset_semanal": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }

    # ================= RESET =================

    @tasks.loop(minutes=30)
    async def reset_missoes(self):
        missoes = load_json(config.MISSOES_FILE, {})
        if not isinstance(missoes, dict):
            missoes = {}

        agora = datetime.utcnow().timestamp()

        for uid in list(missoes.keys()):

            if agora >= missoes[uid].get("reset", 0):
                nivel = missoes[uid].get("nivel", 1)
                missoes[uid] = self.gerar_missoes()
                missoes[uid]["nivel"] = nivel + 1

            if agora >= missoes[uid].get("reset_semanal", 0):
                missoes[uid]["semanal"]["progresso"] = 0
                missoes[uid]["semanal"]["concluida"] = False
                missoes[uid]["reset_semanal"] = (
                    datetime.utcnow() + timedelta(days=7)
                ).timestamp()

        save_json(config.MISSOES_FILE, missoes)

    # ================= BARRA =================

    def barra(self, progresso, meta):
        if meta <= 0:
            return "⬛" * 10
        progresso = min(progresso, meta)
        preenchido = int((progresso / meta) * 10)
        return "🟩" * preenchido + "⬛" * (10 - preenchido)

    # ================= /MISSOES =================

    @app_commands.command(name="missoes", description="Veja suas missões")
    async def ver_missoes(self, interaction: discord.Interaction):

        await interaction.response.defer(thinking=True)

        try:
            missoes = load_json(config.MISSOES_FILE, {})
            if not isinstance(missoes, dict):
                missoes = {}

            uid = str(interaction.user.id)

            if uid not in missoes:
                missoes[uid] = self.gerar_missoes()
                save_json(config.MISSOES_FILE, missoes)

            dados = missoes[uid]

            embed = discord.Embed(
                title=f"🎖 Missões • Nível {dados.get('nivel', 1)}",
                color=config.COLOR_PRIMARY
            )

            for nome in ["mensagens", "evento", "evento_raro", "fragmentos", "call", "semanal"]:
                m = dados.get(nome)
                if not m:
                    continue
                status = "✅" if m.get("concluida") else "❌"
                embed.add_field(
                    name=f"{status} {nome.replace('_', ' ').title()}",
                    value=f"{self.barra(m.get('progresso', 0), m.get('meta', 1))}\n"
                          f"{m.get('progresso', 0)}/{m.get('meta', 1)} • 💎 {m.get('recompensa', 0)}",
                    inline=False
                )

            users = load_json(config.USERS_DB, {})
            user_data = users.get(uid, {})
            conquistas = user_data.get("conquistas", [])
            if conquistas:
                embed.add_field(
                    name="🏆 Conquistas",
                    value=", ".join(conquistas),
                    inline=False
                )

            view = self.ResgatarView(interaction.user.id)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao carregar missões:\n```{e}```")


async def setup(bot):
    await bot.add_cog(Missoes(bot))
