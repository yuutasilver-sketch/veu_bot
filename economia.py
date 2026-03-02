import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
from datetime import datetime
import asyncio
import time

from database import load_json, save_json, ensure_user, iso_to_dt
import config

USERS_DB = config.USERS_DB
LOG_CHANNEL_ID = getattr(config, "TICKET_LOG_CHANNEL_ID", None)

ADD_LOCK = asyncio.Lock()


# =========================
# GARANTIR CARTEIRA
# =========================

def ensure_wallet(data: dict):
    data.setdefault("fragmentos", 0)
    data.setdefault("banco", 0)
    data.setdefault("mensagens", 0)
    data.setdefault("tempo_call", 0)
    data.setdefault("daily_social", 0)
    data.setdefault("vip_until", None)
    return data


# =========================
# VIP
# =========================

def has_vip(data: dict) -> bool:
    dt = iso_to_dt(data.get("vip_until"))
    return bool(dt and dt > datetime.utcnow())


def vip_bonus(valor: int) -> int:
    return int(valor * 0.20)


# =========================
# LOG (EMBED ADMIN)
# =========================

async def send_log_embed(bot, admin, target, quantidade: int):
    if not LOG_CHANNEL_ID:
        return

    ch = bot.get_channel(LOG_CHANNEL_ID)
    if not ch:
        return

    embed = discord.Embed(
        title="📈 ADMIN ADICIONOU FRAGMENTOS",
        color=config.COLOR_SUCCESS,
        timestamp=datetime.utcnow()
    )

    embed.add_field(name="👤 Administrador", value=admin.mention, inline=False)
    embed.add_field(name="🎯 Usuário", value=target.mention, inline=False)
    embed.add_field(
        name="💠 Quantidade",
        value=f"**{quantidade} {config.CURRENCY_NAME}**",
        inline=False
    )

    await ch.send(embed=embed)


# =========================
# VIEW APOSTA
# =========================

class BetConfirmView(discord.ui.View):

    def __init__(self, bot, p1, p2, quantidade: int):
        super().__init__(timeout=120)
        self.bot = bot
        self.p1 = p1
        self.p2 = p2
        self.quantidade = quantidade

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message(
                "Apenas o desafiado pode aceitar.",
                ephemeral=True
            )

        users = load_json(USERS_DB, {})

        p1 = ensure_wallet(ensure_user(users, self.p1.id))
        p2 = ensure_wallet(ensure_user(users, self.p2.id))

        if p1["fragmentos"] < self.quantidade or p2["fragmentos"] < self.quantidade:
            return await interaction.response.send_message(
                "Saldo insuficiente.",
                ephemeral=True
            )

        d1 = random.randint(1, 20)
        d2 = random.randint(1, 20)
        if d1 == d2:
            d2 += 1

        if d1 > d2:
            vencedor = self.p1
            vdata, pdata = p1, p2
        else:
            vencedor = self.p2
            vdata, pdata = p2, p1

        ganho = self.quantidade
        if has_vip(vdata):
            ganho += vip_bonus(self.quantidade)

        vdata["fragmentos"] += ganho
        pdata["fragmentos"] -= self.quantidade

        save_json(USERS_DB, users)

        texto = (
            f"🎲 **Ritual do Véu**\n\n"
            f"{self.p1.mention}: {d1}\n"
            f"{self.p2.mention}: {d2}\n\n"
            f"🏆 {vencedor.mention} ganhou **{ganho} {config.CURRENCY_NAME}**"
        )

        await interaction.response.edit_message(content=texto, view=None)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.red)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message(
                "Apenas o desafiado.",
                ephemeral=True
            )

        await interaction.response.edit_message(
            content="Aposta recusada.",
            view=None
        )


# =========================
# VIEW ADMIN REMOVER
# =========================

class AdminRemoveView(discord.ui.View):

    def __init__(self, target_id: int, quantidade: int):
        super().__init__(timeout=120)
        self.target_id = target_id
        self.quantidade = quantidade

    @discord.ui.button(label="❌ Tirar Fragmentos", style=discord.ButtonStyle.red)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "Apenas administradores.",
                ephemeral=True
            )

        users = load_json(USERS_DB, {})
        data = ensure_wallet(ensure_user(users, self.target_id))

        data["fragmentos"] = max(0, data["fragmentos"] - self.quantidade)
        save_json(USERS_DB, users)

        await interaction.response.send_message("Removido.", ephemeral=True)


# =========================
# COG ECONOMIA
# =========================

class Economia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.call_users = {}
        self.loop_call.start()

    # =========================
    # GANHO POR MENSAGEM
    # =========================

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        users = load_json(USERS_DB, {})
        data = ensure_wallet(ensure_user(users, message.author.id))

        data["fragmentos"] += 2
        data["mensagens"] += 1

        save_json(USERS_DB, users)

    # =========================
    # GANHO POR CALL
    # =========================

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if member.bot:
            return

        if after.channel and not before.channel:
            self.call_users[member.id] = time.time()

        elif before.channel and not after.channel:
            if member.id in self.call_users:
                tempo = time.time() - self.call_users[member.id]
                minutos = int(tempo // 60)

                if minutos > 0:
                    users = load_json(USERS_DB, {})
                    data = ensure_wallet(ensure_user(users, member.id))

                    ganho = minutos * 3
                    data["fragmentos"] += ganho
                    data["tempo_call"] += minutos

                    save_json(USERS_DB, users)

                del self.call_users[member.id]

    @tasks.loop(minutes=5)
    async def loop_call(self):
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    if member.bot:
                        continue
                    if member.id not in self.call_users:
                        self.call_users[member.id] = time.time()

    # =========================
    # DAILY SOCIAL
    # =========================

    @app_commands.command(name="daily_social")
    async def daily_social(self, interaction: discord.Interaction):

        users = load_json(USERS_DB, {})
        data = ensure_wallet(ensure_user(users, interaction.user.id))

        agora = time.time()
        ultimo = data.get("daily_social", 0)

        if agora - ultimo < 86400:
            return await interaction.response.send_message(
                "⏳ Você já coletou hoje.",
                ephemeral=True
            )

        ganho = 250
        data["fragmentos"] += ganho
        data["daily_social"] = agora

        save_json(USERS_DB, users)

        await interaction.response.send_message(
            f"💎 Você recebeu **{ganho} {config.CURRENCY_NAME}**!"
        )


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Economia(bot))
