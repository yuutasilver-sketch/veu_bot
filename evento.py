import discord
from discord.ext import commands  # Corrigido
from discord import app_commands  # Corrigido
import asyncio
import random
from datetime import datetime, timedelta  # Corrigido

from database import load_json, save_json, ensure_user, get_guild_config  # Corrigido
import config

USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB

# =========================
# VIEW PARA DROP
# =========================
class DropView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=60)
        self.valor = valor
        self.claimed = False

    @discord.ui.button(label="Capturar!", style=discord.ButtonStyle.success)
    async def capturar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            return await interaction.response.send_message("❌ Já capturado!", ephemeral=True)

        self.claimed = True
        self.stop()

        users = load_json(USERS_DB, {})
        uid = str(interaction.user.id)
        user = ensure_user(users, uid)
        user["fragmentos"] = user.get("fragmentos", 0) + self.valor
        save_json(USERS_DB, users)

        embed = discord.Embed(
            title="✅ Fragmento Capturado!",
            description=f"Você ganhou {self.valor} fragmentos eternos!",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Evento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # EVENTO: DROP RANDOM
    # =========================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg["drops_enabled"]:
            return

        chance = cfg["drops_chance"]  # % por mensagem

        if random.random() * 100 > chance:
            return

        min_val = cfg["drops_min"]
        max_val = cfg["drops_max"]

        valor = random.randint(min_val, max_val)

        embed = discord.Embed(
            title="✨ Fragmento do Véu Detectado!",
            description="Clique primeiro para capturar!",
            color=0x5865F2
        )

        view = DropView(valor)

        await message.channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Evento(bot))