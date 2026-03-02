import discord
from discord.ext import commands, tasks
import time
import random

import config
from database import load_json, save_json, ensure_user


USERS_DB = config.USERS_DB


# =========================
# CONFIG DO SISTEMA
# =========================

MAX_LEVEL = 100

XP_BASE = 300
XP_MULT = 1.32

XP_MSG_MIN = 10
XP_MSG_MAX = 18

XP_CALL_PER_MIN = 12

MSG_COOLDOWN = 25

LEVEL_REWARD = 120

LEVEL_UP_CHANNEL = config.LEVEL_UP_CHANNEL


# =========================
# CARGOS TEMÁTICOS
# =========================

LEVEL_ROLES = {
    10: "✦ Portador do Fragmento",
    20: "✦ Desperto do Véu",
    30: "✦ Andarilho Dimensional",
    40: "✦ Guardião das Fendas",
    50: "✦ Arauto dos Ecos",
    60: "✦ Mestre do Limiar",
    70: "✦ Arconte Velado",
    80: "✦ Senhor das Realidades",
    90: "✦ Soberano do Véu",
    100: "✦ Entidade Primordial"
}


# =========================
# XP NECESSÁRIO
# =========================

def xp_needed(level: int):
    return int(XP_BASE * (XP_MULT ** level))


# =========================
# DAR XP + LEVEL UP
# =========================

async def give_xp(member, amount: int, guild):

    users = load_json(USERS_DB, {})
    data = ensure_user(users, member.id)

    data.setdefault("level", 0)
    data.setdefault("xp", 0)
    data.setdefault("fragmentos", 0)

    if data["level"] >= MAX_LEVEL:
        return

    data["xp"] += amount

    leveled_up = False

    while data["xp"] >= xp_needed(data["level"]):
        data["xp"] -= xp_needed(data["level"])
        data["level"] += 1
        data["fragmentos"] += LEVEL_REWARD
        leveled_up = True

        if data["level"] >= MAX_LEVEL:
            data["level"] = MAX_LEVEL
            data["xp"] = 0
            break

    save_json(USERS_DB, users)

    if leveled_up:
        await level_up(member, data["level"], guild)


# =========================
# EVENTO LEVEL UP
# =========================

async def level_up(member, level, guild):

    channel = guild.get_channel(LEVEL_UP_CHANNEL)
    if not channel:
        return

    role = await ensure_level_role(guild, level)

    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            pass

    await channel.send(
        f"🌌 **{member.mention} atravessou o Véu e alcançou o Nível {level}!**\n"
        f"✨ Fragmentos recebidos: {LEVEL_REWARD}"
    )


# =========================
# CRIAR CARGO AUTOMÁTICO
# =========================

async def ensure_level_role(guild, level):

    if level not in LEVEL_ROLES:
        return None

    name = LEVEL_ROLES[level]

    role = discord.utils.get(guild.roles, name=name)

    if role:
        return role

    try:
        role = await guild.create_role(
            name=name,
            colour=discord.Colour.purple(),
            mentionable=False,
            reason="Cargo automático do sistema de nível"
        )
        return role
    except discord.Forbidden:
        return None


# =========================
# COG PRINCIPAL
# =========================

class LevelSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_xp.start()

    # =========================
    # XP POR MENSAGEM
    # =========================

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        users = load_json(USERS_DB, {})
        data = ensure_user(users, message.author.id)

        data.setdefault("xp_last_msg", 0)

        now = time.time()

        if now - data["xp_last_msg"] < MSG_COOLDOWN:
            await self.bot.process_commands(message)
            return

        xp = random.randint(XP_MSG_MIN, XP_MSG_MAX)

        data["xp_last_msg"] = now
        save_json(USERS_DB, users)

        await give_xp(message.author, xp, message.guild)

        # 🔥 ESSENCIAL PRA NÃO QUEBRAR COMANDOS
        await self.bot.process_commands(message)

    # =========================
    # XP POR CALL
    # =========================

    @tasks.loop(minutes=1)
    async def voice_xp(self):

        for guild in self.bot.guilds:

            for vc in guild.voice_channels:

                # ❌ evita farm sozinho
                if len(vc.members) < 2:
                    continue

                for member in vc.members:

                    if member.bot:
                        continue

                    await give_xp(member, XP_CALL_PER_MIN, guild)

    @voice_xp.before_loop
    async def before_voice(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(LevelSystem(bot))