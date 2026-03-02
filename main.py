# bot.py
import discord
from discord.ext import commands
import asyncio
import time
import os
from datetime import datetime, timezone

import config
from database import load_json, save_json, ensure_user

# 🔥 IMPORTANTE PARA VIEW PERSISTENTE
from loja import LojaView

# Adicione pra API backend
from aiohttp import web

# =========================
# GARANTIA DE PASTAS
# =========================
os.makedirs(getattr(config, "GENERATED_PROFILES_PATH", "generated"), exist_ok=True)
os.makedirs(config.BASE_DATA, exist_ok=True)

# =========================
# INTENTS
# =========================
intents = discord.Intents.all()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
vip_loop_started = False

# =========================
# EXTENSIONS
# =========================
async def load_all():
    extensions = [
        "ajuda",
        "announcements",
        "anonymous",
        "autorole",
        "call_manager",
        "daily",
        "economia",
        "evento",
        "gifts",
        "level_system",
        "loja",
        "loja_cor",
        "missoes",
        "perfil",
        "ranking",
        "social",
        "ticket",
        "weekly",
    ]

    for ext in extensions:
        await bot.load_extension(ext)
        print(f"⚡ Extensão {ext} carregada")

# =========================
# ON READY
# =========================
@bot.event
async def on_ready():
    print(f"🔥 Véu conectada como {bot.user} ({bot.user.id})")

    # 🔥 REGISTRA A VIEW PERSISTENTE DA LOJA
    bot.add_view(LojaView())

    # ⭐ SYNC SLASH (mantém como você tinha)
    try:
        synced = await bot.tree.sync()
        print(f"⚡ {len(synced)} slash sincronizados GLOBAL")

        for guild in bot.guilds:
            gsynced = await bot.tree.sync(guild=guild)
            print(f"⚡ {len(gsynced)} sincronizados em {guild.name}")

    except Exception as e:
        print("❌ ERRO SLASH:", e)

    if not vip_loop_started:
        bot.loop.create_task(vip_checker_loop())
        vip_loop_started = True

    print("=========================\n")

# =========================
# START
# =========================
async def main():
    async with bot:
        await load_all()
        bot.loop.create_task(start_api())  # Inicia a API backend
        await bot.start(config.TOKEN)

# =========================
# BACKEND API
# =========================
async def start_api():
    app = web.Application()
    app.router.add_get('/token', handle_token)
    app.router.add_post('/api/config/{guild_id}', handle_config)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', config.API_PORT)  # Usa PORT da Vertra
    await site.start()
    print(f"🔥 API backend rodando na porta {config.API_PORT}")

async def handle_token(request):
    code = request.query.get('code')
    if not code:
        return web.json_response({'error': 'Código não encontrado'}, status=400)

    data = {
        'client_id': config.DISCORD_CLIENT_ID,
        'client_secret': config.DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://veu-entre-mundos.netlify.app/callback'  # Seu site na Netlify
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    async with aiohttp.ClientSession() as session:
        async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as resp:
            token_data = await resp.json()
            return web.json_response(token_data, status=resp.status)

async def handle_config(request):
    guild_id = request.match_info['guild_id']
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return web.json_response({'error': 'Não autorizado'}, status=401)

    try:
        config_data = await request.json()
    except:
        return web.json_response({'error': 'Dados inválidos'}, status=400)

    # Salva no GUILDS_DB
    guilds = load_json(config.GUILDS_DB, {})
    if guild_id not in guilds:
        guilds[guild_id] = config.DEFAULT_GUILD_CONFIG.copy()

    guilds[guild_id].update(config_data)
    save_json(config.GUILDS_DB, guilds)

    return web.json_response({'success': True, 'message': 'Configs salvas!'})

asyncio.run(main())