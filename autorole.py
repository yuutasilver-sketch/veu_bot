import discord
from discord.ext import commands
from datetime import datetime, timedelta
import config


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===============================
    # EVENTO: MEMBRO ENTROU
    # ===============================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        # Ignorar bots
        if member.bot:
            return

        guild = member.guild

        # ===============================
        # CARGO PADRÃO
        # ===============================
        try:
            default_role = guild.get_role(config.DEFAULT_ROLE_ID)
            if default_role:
                await member.add_roles(
                    default_role,
                    reason="AutoRole: cargo padrão"
                )
        except Exception:
            pass

        # ===============================
        # CONTA NOVA / ANTIGA
        # ===============================
        try:
            account_age = datetime.utcnow() - member.created_at

            # Conta nova (menos de 7 dias)
            if hasattr(config, "NEW_ACCOUNT_ROLE_ID"):
                if account_age < timedelta(days=7):
                    role = guild.get_role(config.NEW_ACCOUNT_ROLE_ID)
                    if role:
                        await member.add_roles(
                            role,
                            reason="AutoRole: conta nova"
                        )

            # Conta antiga
            if hasattr(config, "OLD_ACCOUNT_ROLE_ID"):
                if account_age >= timedelta(days=7):
                    role = guild.get_role(config.OLD_ACCOUNT_ROLE_ID)
                    if role:
                        await member.add_roles(
                            role,
                            reason="AutoRole: conta antiga"
                        )
        except Exception:
            pass

        # ===============================
        # VIP AUTOMÁTICO (se já tiver)
        # ===============================
        try:
            if hasattr(config, "VIP_ROLE_ID"):
                vip_role = guild.get_role(config.VIP_ROLE_ID)

                if vip_role and vip_role in member.roles:
                    await member.add_roles(
                        vip_role,
                        reason="AutoRole: VIP automático"
                    )
        except Exception:
            pass


# ===============================
# SETUP DO COG
# ===============================
async def setup(bot):
    await bot.add_cog(AutoRole(bot))