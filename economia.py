# economia.py — ECONOMIA DO VÉU (MULTI-SERVIDOR + IMERSIVA)

import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta
import asyncio

from database import (
    load_json, save_json, ensure_user, iso_to_dt, get_guild_config,
    now_iso, is_premium, premium_message, is_vip  # Adicione is_vip se ainda não tiver
)
import config

USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB

ADD_LOCK = asyncio.Lock()

# Configurações de recompensas (pode vir da dashboard depois)
DAILY_REWARD_BASE = 300
DAILY_VIP_BONUS = 1.5  # 50% extra para VIP

WEEKLY_REWARD_BASE = 1500
WEEKLY_VIP_BONUS = 1.5  # 50% extra para VIP

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /saldo
    @app_commands.command(name="saldo", description="Contemple seus fragmentos eternos no Véu")
    async def saldo(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        users = load_json(USERS_DB, {})
        user = ensure_user(users, str(target.id))

        embed = discord.Embed(
            title=f"💎 Fragmentos de {target.display_name}",
            description=f"**{user.get('fragmentos', 0):,} fragmentos eternos**",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Véu Entre Mundos • Sua riqueza entre mundos ♾️")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # /daily
    @app_commands.command(name="daily", description="Resgate sua oferenda diária do Véu")
    async def daily(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        user_id = str(interaction.user.id)

        async with ADD_LOCK:
            users = load_json(USERS_DB, {})
            user = ensure_user(users, user_id)

            agora = datetime.fromisoformat(now_iso())
            ultimo_daily = iso_to_dt(user["cooldowns"].get("daily"))

            if ultimo_daily and (agora - ultimo_daily) < timedelta(days=1):
                proximo = ultimo_daily + timedelta(days=1)
                tempo_restante = proximo - agora
                horas = tempo_restante.seconds // 3600
                minutos = (tempo_restante.seconds % 3600) // 60
                embed = discord.Embed(
                    title="⏳ O Véu ainda descansa...",
                    description=f"Volte em {horas}h {minutos}min para a próxima oferenda.",
                    color=config.COLOR_WARNING
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            reward = DAILY_REWARD_BASE
            vip_bonus = ""
            if is_vip(user):
                reward = int(reward * DAILY_VIP_BONUS)
                vip_bonus = "👑 Bônus VIP aplicado! "

            user["fragmentos"] = user.get("fragmentos", 0) + reward
            user["cooldowns"]["daily"] = now_iso()

            save_json(USERS_DB, users)

            embed = discord.Embed(
                title="🌙 Oferenda Diária Resgatada!",
                description=f"Você recebeu **{reward:,} fragmentos**!\n{vip_bonus}\nVolte amanhã para mais.",
                color=config.COLOR_SUCCESS
            )
            embed.set_footer(text="Véu Entre Mundos • Renovação diária ♾️")

            await interaction.response.send_message(embed=embed)

    # /weekly
    @app_commands.command(name="weekly", description="Resgate sua oferenda semanal do Véu")
    async def weekly(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        async with ADD_LOCK:
            users = load_json(USERS_DB, {})
            user = ensure_user(users, user_id)

            agora = datetime.fromisoformat(now_iso())
            ultimo_weekly = iso_to_dt(user["cooldowns"].get("weekly"))

            if ultimo_weekly and (agora - ultimo_weekly) < timedelta(days=7):
                proximo = ultimo_weekly + timedelta(days=7)
                tempo_restante = proximo - agora
                dias = tempo_restante.days
                horas = tempo_restante.seconds // 3600
                embed = discord.Embed(
                    title="🕰️ A eternidade ainda não completou o ciclo...",
                    description=f"Faltam {dias} dias e {horas}h.",
                    color=config.COLOR_WARNING
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            reward = WEEKLY_REWARD_BASE
            vip_bonus = ""
            if is_vip(user):
                reward = int(reward * WEEKLY_VIP_BONUS)
                vip_bonus = "👑 Bônus VIP aplicado! "

            user["fragmentos"] = user.get("fragmentos", 0) + reward
            user["cooldowns"]["weekly"] = now_iso()

            save_json(USERS_DB, users)

            embed = discord.Embed(
                title="🏆 Oferenda Semanal Resgatada!",
                description=f"Você recebeu **{reward:,} fragmentos**!\n{vip_bonus}\nVolte na próxima semana.",
                color=0xFFD700  # Gold
            )
            embed.set_footer(text="Véu Entre Mundos • Dedicação recompensada ♾️")

            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))