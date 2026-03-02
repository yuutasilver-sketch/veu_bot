# level_system.py — SISTEMA DE NÍVEIS DO VÉU (MULTI-SERVIDOR + IMERSIVO)

import discord
from discord.ext import commands, tasks
import time
import random
from datetime import datetime, timedelta, timezone

import config
from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message, vip_days

USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_xp.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        users = load_json(USERS_DB, {})
        user_id = str(message.author.id)
        user = ensure_user(users, user_id)

        last_message = user.get("last_message", 0)
        if time.time() - last_message < 60:
            return

        user["last_message"] = time.time()

        xp_gain = random.randint(15, 25)
        user["xp"] += xp_gain
        user["mensagens"] += 1

        level = user["level"]
        required_xp = 100 * (level + 1) ** 2
        if user["xp"] >= required_xp:
            user["level"] += 1
            user["xp"] -= required_xp

            embed = discord.Embed(
                title="Ascensão no Véu!",
                description=f"{message.author.mention} ascendeu ao nível {user['level']}!",
                color=0x4b0082,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Véu Entre Mundos • Nível ascendente ♾️")
            await message.channel.send(embed=embed)

        await save_json(USERS_DB, users)

    @tasks.loop(seconds=60)
    async def voice_xp(self):
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if not vc.members:
                    continue

                users = load_json(USERS_DB, {})
                for member in vc.members:
                    if member.bot:
                        continue

                    user_id = str(member.id)
                    user = ensure_user(users, user_id)

                    xp_gain = random.randint(5, 10)
                    user["xp"] += xp_gain

                    level = user["level"]
                    required_xp = 100 * (level + 1) ** 2
                    if user["xp"] >= required_xp:
                        user["level"] += 1
                        user["xp"] -= required_xp

                        embed = discord.Embed(
                            title="Ascensão no Véu!",
                            description=f"{member.mention} ascendeu ao nível {user['level']} em voice!",
                            color=0x4b0082,
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.set_footer(text="Véu Entre Mundos • Nível ascendente ♾️")

                        text_channel = guild.text_channels[0]
                        await text_channel.send(embed=embed)

                await save_json(USERS_DB, users)

    @voice_xp.before_loop
    async def before_voice(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))