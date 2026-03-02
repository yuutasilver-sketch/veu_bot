# missoes.py — SISTEMA DE MISSÕES (MULTI-SERVIDOR + DASHBOARD)

import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
from datetime import datetime, timedelta

import config
from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message, now_iso, iso_to_dt

USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB


# =========================
# MISSÕES PADRÃO (fallback, editável via dashboard)
# =========================
DEFAULT_MISSOES = {
    "daily": [
        {"nome": "Mensageiro do Véu", "tipo": "mensagens", "meta": 50, "recompensa": 200, "descricao": "Envie 50 mensagens em canais de texto."},
        {"nome": "Voz Eterna", "tipo": "calls", "meta": 60, "recompensa": 300, "descricao": "Fique 60 minutos em chamadas de voz."},
        {"nome": "Reacionário", "tipo": "reacoes", "meta": 20, "recompensa": 150, "descricao": "Adicione 20 reações a mensagens."}
    ],
    "weekly": [
        {"nome": "Explorador Semanal", "tipo": "mensagens", "meta": 500, "recompensa": 2000, "descricao": "Envie 500 mensagens na semana."},
        {"nome": "Guardião das Vozes", "tipo": "calls", "meta": 300, "recompensa": 2500, "descricao": "Fique 300 minutos em calls na semana."}
    ]
}


# =========================
# GARANTIR CAMPOS DE MISSÕES NO USER (GLOBAL)
# =========================
def ensure_missoes(user: dict, tipo: str = "daily"):
    user.setdefault("missoes", {})
    user["missoes"].setdefault(tipo, {})
    for missao in DEFAULT_MISSOES.get(tipo, []):
        user["missoes"][tipo].setdefault(missao["nome"], {"progresso": 0, "completada": False})
    user.setdefault("cooldowns", {})
    user["cooldowns"].setdefault(f"last_{tipo}_reset", None)


# =========================
# VIEW PARA RESGATAR MISSÕES
# =========================
class ResgatarView(discord.ui.View):
    def __init__(self, user_id, guild_id, tipo="daily"):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.tipo = tipo

    @discord.ui.button(label="Resgatar Recompensas", style=discord.ButtonStyle.success, emoji="🏆")
    async def resgatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Apenas você pode resgatar suas próprias recompensas.", ephemeral=True)

        users = load_json(USERS_DB, {})
        user = ensure_user(users, self.user_id)
        ensure_missoes(user, self.tipo)

        cfg = get_guild_config(self.guild_id)

        if not cfg.get("missoes_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        total_recompensa = 0
        missoes = cfg.get(f"{self.tipo}_missoes", DEFAULT_MISSOES.get(self.tipo, []))

        for m in missoes:
            nome = m["nome"]
            progresso = user["missoes"][self.tipo].get(nome, {}).get("progresso", 0)
            meta = m.get("meta", 1)
            if progresso >= meta and not user["missoes"][self.tipo][nome]["completada"]:
                total_recompensa += m.get("recompensa", 0)
                user["missoes"][self.tipo][nome]["completada"] = True

        if total_recompensa > 0:
            user["fragmentos"] += total_recompensa
            save_json(USERS_DB, users)
            await interaction.response.send_message(
                f"✨ Recompensas resgatadas! Você ganhou **{total_recompensa} fragmentos** do Véu.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Nenhuma missão completada para resgatar.", ephemeral=True)


# =========================
# COG MISSÕES
# =========================
class Missoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset_daily.start()
        self.reset_weekly.start()

    def cog_unload(self):
        self.reset_daily.cancel()
        self.reset_weekly.cancel()

    # =========================
    # RESET DIÁRIO/SEMANAL
    # =========================
    @tasks.loop(hours=24)
    async def reset_daily(self):
        users = load_json(USERS_DB, {})
        for uid, user in users.items():
            ensure_missoes(user, "daily")
            last_reset = iso_to_dt(user["cooldowns"].get("last_daily_reset"))
            if not last_reset or (datetime.utcnow() - last_reset) >= timedelta(days=1):
                for missao in user["missoes"]["daily"].values():
                    missao["progresso"] = 0
                    missao["completada"] = False
                user["cooldowns"]["last_daily_reset"] = now_iso()
        save_json(USERS_DB, users)

    @tasks.loop(hours=168)  # 7 dias
    async def reset_weekly(self):
        users = load_json(USERS_DB, {})
        for uid, user in users.items():
            ensure_missoes(user, "weekly")
            last_reset = iso_to_dt(user["cooldowns"].get("last_weekly_reset"))
            if not last_reset or (datetime.utcnow() - last_reset) >= timedelta(days=7):
                for missao in user["missoes"]["weekly"].values():
                    missao["progresso"] = 0
                    missao["completada"] = False
                user["cooldowns"]["last_weekly_reset"] = now_iso()
        save_json(USERS_DB, users)

    @reset_daily.before_loop
    @reset_weekly.before_loop
    async def before_reset(self):
        await self.bot.wait_until_ready()

    # =========================
    # UPDATE PROGRESSO (exemplos)
    # =========================
    async def update_missao(self, user_id, missao_tipo, quantidade=1):
        users = load_json(USERS_DB, {})
        user = ensure_user(users, user_id)
        ensure_missoes(user, "daily")
        ensure_missoes(user, "weekly")

        for tipo in ["daily", "weekly"]:
            for missao in user["missoes"][tipo].values():
                if missao["tipo"] == missao_tipo and not missao["completada"]:
                    missao["progresso"] += quantidade

        save_json(USERS_DB, users)

    # Listener para mensagens (missão de mensagens)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("missoes_enabled", True):
            return

        await self.update_missao(message.author.id, "mensagens")

    # Listener para reações (missão de reações)
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or not reaction.message.guild:
            return

        guild_id = reaction.message.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("missoes_enabled", True):
            return

        await self.update_missao(user.id, "reacoes")

    # Para calls: integre com call_manager.py ou adicione listener similar (ex: a cada minuto em voice)

    # =========================
    # COMANDO /missoes
    # =========================
    @app_commands.command(name="missoes", description="Ver suas missões diárias/semanal e progresso")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Diárias", value="daily"),
        app_commands.Choice(name="Semanais", value="weekly")
    ])
    async def missoes(self, interaction: discord.Interaction, tipo: str = "daily"):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("missoes_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        users = load_json(USERS_DB, {})
        user = ensure_user(users, interaction.user.id)
        ensure_missoes(user, tipo)

        missoes = cfg.get(f"{tipo}_missoes", DEFAULT_MISSOES.get(tipo, []))

        embed = discord.Embed(
            title=f"✨ Missões {tipo.capitalize()} do Véu",
            description="Complete desafios para ganhar fragmentos eternos!",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.utcnow()
        )

        for m in missoes:
            nome = m["nome"]
            progresso_data = user["missoes"][tipo].get(nome, {"progresso": 0})
            progresso = progresso_data["progresso"]
            meta = m.get("meta", 1)
            recompensa = m.get("recompensa", 0)
            completada = progresso_data.get("completada", False)
            status = "✅ Completada" if completada else f"{progresso}/{meta}"

            embed.add_field(
                name=f"{nome}",
                value=f"{m['descricao']}\nProgresso: {status} • Recompensa: 💎 {recompensa}",
                inline=False
            )

        view = ResgatarView(interaction.user.id, guild_id, tipo)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Missoes(bot))