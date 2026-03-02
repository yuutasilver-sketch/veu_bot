# main.py — VÉU ENTRE MUNDOS (GLOBAL + BACKEND + MULTI SERVIDOR)

import discord
from discord.ext import commands
import asyncio
import os
import logging
from aiohttp import web

import config
from database import load_json, save_json, ensure_guild

# ─────────────────────────────
# LOG
# ─────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("VeuBot")

# ─────────────────────────────
# BOT CONFIG
# ─────────────────────────────

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents
)

# ─────────────────────────────
# EVENTOS DO BOT
# ─────────────────────────────

@bot.event
async def on_ready():
    logger.info(f"Bot online como {bot.user}")
    logger.info(f"Total de servidores: {len(bot.guilds)}")

@bot.event
async def on_guild_join(guild):
    ensure_guild(str(guild.id))
    logger.info(f"Entrou no servidor: {guild.name}")

# ─────────────────────────────
# API BACKEND (PORTA 80 FIXA)
# ─────────────────────────────

app = web.Application()

# Health check obrigatório
async def health(request):
    return web.Response(text="Veu backend online")

app.router.add_get("/", health)

# Retorna guilds do bot
async def get_guilds(request):
    guild_list = [
        {
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None
        }
        for guild in bot.guilds
    ]
    return web.json_response(guild_list)

app.router.add_get("/guilds", get_guilds)

# Atualiza config da guild
async def update_config(request):
    guild_id = request.match_info["guild_id"]
    data = await request.json()

    guilds = load_json(config.GUILDS_DB)

    if guild_id not in guilds:
        ensure_guild(guild_id)
        guilds = load_json(config.GUILDS_DB)

    guilds[guild_id].update(data)
    save_json(config.GUILDS_DB, guilds)

    return web.json_response({"success": True})

app.router.add_post("/config/{guild_id}", update_config)

# ─────────────────────────────
# INICIAR API NA PORTA 80
# ─────────────────────────────

async def start_api():
    runner = web.AppRunner(app)
    await runner.setup()

    try:
        site = web.TCPSite(runner, "0.0.0.0", 80)
        await site.start()
        logger.info("API iniciada na porta 80")
    except Exception as e:
        logger.error(f"Erro ao iniciar API: {e}")

# ─────────────────────────────
# MAIN
# ─────────────────────────────

async def main():
    await start_api()
    await bot.start(config.TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
