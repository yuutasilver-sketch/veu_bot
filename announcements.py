import discord
from discord.ext import commands, tasks  # Corrigido
from database import load_json, get_guild_config, get_guild_plan, now_iso, save_json  # Corrigido e adicionado now_iso/save_json
import config
from datetime import datetime  # Corrigido


class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announce_task.start()

    def cog_unload(self):
        self.announce_task.cancel()

    # ==================================================
    # 🔔 ANÚNCIOS AUTOMÁTICOS (per guild interval)
    # ==================================================
    @tasks.loop(hours=1)  # Check a cada hora, mas envia de acordo com interval per guild
    async def announce_task(self):

        guilds_data = load_json(config.GUILDS_DB, {})
        for guild_id_str in guilds_data:
            guild_id = int(guild_id_str)
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            cfg = get_guild_config(guild_id)  # Usando get_guild_config para consistência
            if not cfg["announce_enabled"]:
                continue

            last_announce = cfg.get("last_announce", None)
            interval = cfg["announce_interval"]  # From dashboard

            if last_announce:
                last_dt = iso_to_dt(last_announce)  # Use iso_to_dt de database
                if (datetime.utcnow() - last_dt) < timedelta(hours=interval):
                    continue

            channel_id = cfg["announce_channel"]
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            message = cfg["announce_message"]

            embed = discord.Embed(
                title="🕯️ Anúncio do Véu",
                description=message,
                color=0x6a0dad,
                timestamp=datetime.now()
            )

            await channel.send(embed=embed)

            cfg["last_announce"] = now_iso()
            guilds_data[guild_id_str] = cfg  # Atualiza
            save_json(config.GUILDS_DB, guilds_data)

    # ==================================================
    # 👤 PEGAR NOME DO MEMBRO (opcional)
    # ==================================================
    def get_member_name(self, guild, uid):
        member = guild.get_member(int(uid))
        if member:
            return member.display_name
        return f"ID{uid}"

async def setup(bot):
    await bot.add_cog(Announcements(bot))