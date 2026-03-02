# call_manager.py — GERENCIADOR DE TEMPO EM CALL (MULTI-SERVIDOR + IMERSIVO)

import time
import discord
from discord.ext import commands

from database import load_json, save_json, ensure_user, get_guild_config
from config import USERS_DB, CALLS_DB

class CallManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("🔥 CallManager GLOBAL carregado com sucesso")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        user_id = str(member.id)
        users = load_json(USERS_DB, {})

        # Entrou em voice
        if after.channel and not before.channel:
            # Salva hora de entrada
            CALLS_DB[str(member.guild.id)] = CALLS_DB.get(str(member.guild.id), {})
            CALLS_DB[str(member.guild.id)][user_id] = time.time()
            await save_json(CALLS_DB, CALLS_DB)

        # Saiu de voice
        elif before.channel and not after.channel:
            guild_id = str(member.guild.id)
            if guild_id in CALLS_DB and user_id in CALLS_DB[guild_id]:
                start_time = CALLS_DB[guild_id][user_id]
                elapsed = time.time() - start_time
                user = ensure_user(users, user_id)
                user["tempo_call"] = user.get("tempo_call", 0) + int(elapsed)
                await save_json(USERS_DB, users)
                del CALLS_DB[guild_id][user_id]
                if not CALLS_DB[guild_id]:
                    del CALLS_DB[guild_id]
                await save_json(CALLS_DB, CALLS_DB)

        # Mudou de canal (mantém tempo)
        elif before.channel and after.channel and before.channel != after.channel:
            guild_id = str(member.guild.id)
            if guild_id in CALLS_DB and user_id in CALLS_DB[guild_id]:
                start_time = CALLS_DB[guild_id][user_id]
                elapsed = time.time() - start_time
                user = ensure_user(users, user_id)
                user["tempo_call"] = user.get("tempo_call", 0) + int(elapsed)
                CALLS_DB[guild_id][user_id] = time.time()  # Reset start time
                await save_json(USERS_DB, users)
                await save_json(CALLS_DB, CALLS_DB)

    # Limpa sessões antigas ao iniciar
    async def cog_load(self):
        users = load_json(USERS_DB, {})
        calls = load_json(CALLS_DB, {})
        for guild_id in calls:
            for user_id in calls[guild_id]:
                user = ensure_user(users, user_id)
                user["tempo_call"] = user.get("tempo_call", 0) + 60  # Aproximação
        await save_json(USERS_DB, users)
        await save_json(CALLS_DB, {})
        print("🧹 Sessões de call antigas limpas e tempo salvo após reinício")

        print(f"✅ CallManager pronto! {len(self.bot.guilds)} servidores monitorados.")

async def setup(bot):
    cog = CallManager(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
