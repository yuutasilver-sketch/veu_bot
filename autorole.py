import discord
from discord.ext import commands  # Corrigido
from datetime import datetime, timedelta  # Corrigido
from datetime import timezone  # Adicionado para tz=timezone.utc

from database import load_json, get_guild_config  # Corrigido
import config

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # EVENTO: MEMBRO ENTROU
    # =========================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        if member.bot:
            return

        guild = member.guild
        guild_id = guild.id

        cfg = get_guild_config(guild_id)

        roles_to_add = []

        # Cargos por tempo de conta
        time_roles = cfg["autorole_time_roles"]  # List from dashboard [{"days": 7, "role_id": 123}]

        account_age = datetime.now(tz=timezone.utc) - member.created_at

        for tr in time_roles:
            days = tr.get("days", 0)
            role_id = tr.get("role_id")
            if role_id and account_age >= timedelta(days=days):
                role = guild.get_role(role_id)
                if role:
                    roles_to_add.append(role)

        # Cargo VIP automático
        vip_role_id = cfg["autorole_vip"]
        users = load_json(config.USERS_DB, {})
        uid = str(member.id)
        user = ensure_user(users, uid)
        if vip_role_id and is_vip(user):  # Usando a nova função de database.py
            role = guild.get_role(vip_role_id)
            if role:
                roles_to_add.append(role)

        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Véu AutoRole")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))