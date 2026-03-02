import discord
from discord.ext import commands, tasks
from database import load_json
import config
from datetime import datetime, timedelta

class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announce_task.start()

    def cog_unload(self):
        self.announce_task.cancel()

    @tasks.loop(minutes=10)
    async def announce_task(self):
        canal_id = getattr(config, "ANNOUNCE_CHANNEL_ID", None)
        if not canal_id:
            return

        canal = self.bot.get_channel(canal_id)
        if not canal:
            return

        users = load_json(config.USERS_DB, {})

        agora = datetime.utcnow()
        hoje = agora.date()

        # =========================
        # Top da semana: fragmentos
        # =========================
        top_fragmentos = sorted(users.items(), key=lambda x: x[1].get("fragmentos", 0), reverse=True)[:3]
        if top_fragmentos:
            embed = discord.Embed(
                title="🏆 Top da Semana • Fragmentos",
                description="\n".join(
                    [f"🥇 {self.get_member_name(uid)} — 💎 {data.get('fragmentos',0)}" 
                     for uid, data in top_fragmentos]
                ),
                color=config.COLOR_PRIMARY,
                timestamp=agora
            )
            embed.set_footer(text="Véu Entre Mundos • Ranking Semanal")
            await canal.send(embed=embed)

        # =========================
        # Novos VIPs
        # =========================
        vip_role_id = getattr(config, "VIP_ROLE_ID", None)
        if vip_role_id:
            for guild in self.bot.guilds:
                vip_role = guild.get_role(vip_role_id)
                if vip_role:
                    novos_vips = [m for m in vip_role.members if (datetime.utcnow() - m.joined_at).days < 7]
                    if novos_vips:
                        embed = discord.Embed(
                            title="💎 Novos VIPs da Semana",
                            description="\n".join([m.mention for m in novos_vips]),
                            color=0xFFD700,
                            timestamp=agora
                        )
                        embed.set_footer(text="Véu Entre Mundos • VIPs Recentes")
                        await canal.send(embed=embed)

        # =========================
        # Eventos ativos
        # =========================
        eventos = ["Evento Normal", "Evento Raro", "Evento Amaldiçoado", "Evento Falso"]
        embed = discord.Embed(
            title="⚡ Eventos Ativos da Véu",
            description="\n".join([f"• {ev}" for ev in eventos]),
            color=0x9b59b6,
            timestamp=agora
        )
        embed.set_footer(text="Véu Entre Mundos • Acompanhe os eventos")
        await canal.send(embed=embed)

    # =========================
    # Função utilitária para pegar nome de usuário
    # =========================
    def get_member_name(self, uid):
        for guild in self.bot.guilds:
            member = guild.get_member(int(uid))
            if member:
                return member.display_name
        return f"ID{uid}"

async def setup(bot):
    await bot.add_cog(Announcements(bot))