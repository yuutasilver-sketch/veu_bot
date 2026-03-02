import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import config
from database import load_json, save_json, ensure_user

USERS_DB = config.USERS_DB


class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # FUNÇÃO AUXILIAR: ADICIONAR FRAGMENTOS
    # ==========================================
    def add_fragments(self, user_id: str, amount: int):
        data = load_json(USERS_DB)
        ensure_user(data, user_id)

        data[user_id]["fragmentos"] += amount
        save_json(USERS_DB, data)

    # ==========================================
    # /daily
    # ==========================================
    @app_commands.command(name="daily", description="Receba sua recompensa diária.")
    async def daily(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)
        data = load_json(USERS_DB)
        ensure_user(data, user_id)

        now = datetime.utcnow()

        last_daily = data[user_id].get("ultimo_daily")
        streak = data[user_id].get("streak_daily", 0)

        if last_daily:
            last_daily = datetime.fromisoformat(last_daily)
            diff = now - last_daily

            if diff < timedelta(hours=24):
                remaining = timedelta(hours=24) - diff
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes = remainder // 60

                await interaction.response.send_message(
                    f"⏳ Você já resgatou seu daily.\n"
                    f"Tente novamente em {hours}h {minutes}m.",
                    ephemeral=True
                )
                return

            # Se passou mais de 48h, reseta streak
            if diff > timedelta(hours=48):
                streak = 0

        # Atualiza streak
        streak += 1
        data[user_id]["streak_daily"] = streak
        data[user_id]["ultimo_daily"] = now.isoformat()

        # Recompensa base
        reward = config.DAILY_REWARD

        # Bônus por streak (5% por dia até 7 dias)
        bonus_streak = min(streak, 7) * 0.05
        reward += int(config.DAILY_REWARD * bonus_streak)

        # Bônus VIP
        if hasattr(config, "VIP_ROLE_ID"):
            vip_role = interaction.guild.get_role(config.VIP_ROLE_ID)
            if vip_role and vip_role in interaction.user.roles:
                reward += int(config.DAILY_REWARD * 0.20)

        data[user_id]["fragmentos"] += reward
        save_json(USERS_DB, data)

        embed = discord.Embed(
            title="🎁 Daily Resgatado!",
            description=(
                f"💎 Você recebeu **{reward} fragmentos**!\n\n"
                f"🔥 Streak atual: **{streak} dias**"
            ),
            color=discord.Color.purple(),
            timestamp=now
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # /weekly
    # ==========================================
    @app_commands.command(name="weekly", description="Receba sua recompensa semanal.")
    async def weekly(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)
        data = load_json(USERS_DB)
        ensure_user(data, user_id)

        now = datetime.utcnow()
        last_weekly = data[user_id].get("ultimo_weekly")

        if last_weekly:
            last_weekly = datetime.fromisoformat(last_weekly)
            diff = now - last_weekly

            if diff < timedelta(days=7):
                remaining = timedelta(days=7) - diff
                days = remaining.days
                hours = remaining.seconds // 3600

                await interaction.response.send_message(
                    f"⏳ Você já resgatou seu weekly.\n"
                    f"Tente novamente em {days}d {hours}h.",
                    ephemeral=True
                )
                return

        reward = config.WEEKLY_REWARD

        # Bônus VIP
        if hasattr(config, "VIP_ROLE_ID"):
            vip_role = interaction.guild.get_role(config.VIP_ROLE_ID)
            if vip_role and vip_role in interaction.user.roles:
                reward += int(config.WEEKLY_REWARD * 0.25)

        data[user_id]["fragmentos"] += reward
        data[user_id]["ultimo_weekly"] = now.isoformat()

        save_json(USERS_DB, data)

        embed = discord.Embed(
            title="🏆 Weekly Resgatado!",
            description=(
                f"💎 Você recebeu **{reward} fragmentos**!\n"
                f"Volte na próxima semana para mais recompensas!"
            ),
            color=discord.Color.gold(),
            timestamp=now
        )

        await interaction.response.send_message(embed=embed)


# ==========================================
# SETUP
# ==========================================
async def setup(bot):
    await bot.add_cog(Daily(bot))