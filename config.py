# config.py
import os
import json

# ─────────────────────────────
# BOT
# ─────────────────────────────

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN não encontrado no ambiente")

GUILD_ID = 1462160787530580153


# ─────────────────────────────
# CORES PADRÃO
# ─────────────────────────────

COLOR_PRIMARY = 0x8A2BE2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xF1C40F
COLOR_INFO = 0x3498DB

# ─────────────────────────────
# IDs FIXOS
# ─────────────────────────────

DEFAULT_ROLE_ID = 1462160787530580153  # cargo padrão
VIP_ROLE_ID = 1466167038744461374  # exemplo VIP

ANNOUNCE_CHANNEL_ID = 1462160787530580153  # canal anúncios

TICKET_LOG_CHANNEL_ID = 1462160787530580153  # logs tickets

LEVEL_UP_CHANNEL = 1462160787530580153  # canal level up

# ─────────────────────────────
# ECONOMIA
# ─────────────────────────────

CURRENCY_NAME = "Fragmentos"

BANK_MAX = 1000000

BANK_TAX = 0.05

# ─────────────────────────────
# NÍVEIS
# ─────────────────────────────

LEVEL_ROLES = {  # cargos por nível
    5: 1462160787530580153,
    10: 1462160787530580153,
    20: 1462160787530580153,
}

# ─────────────────────────────
# MISSOES
# ─────────────────────────────

MISSOES = [  # exemplo missões
    {"name": "Mensagens Diárias", "goal": 50, "reward": 500},
    {"name": "Tempo em Call", "goal": 60, "reward": 800},
]

# ─────────────────────────────
# TICKETS
# ─────────────────────────────

TICKET_PANEL_TEXT = "Abra um ticket para suporte."

TICKET_IMAGE_URL = "https://exemplo.com/imagem.png"

# ─────────────────────────────
# PASTAS
# ─────────────────────────────

BASE_DATA = "database"

USERS_DB = f"{BASE_DATA}/users.json"
CALLS_DB = f"{BASE_DATA}/calls.json"
SHOP_DB = f"{BASE_DATA}/shop.json"
TICKETS_DB = f"{BASE_DATA}/tickets.json"
MISSOES_DB = f"{BASE_DATA}/missoes.json"

GENERATED_PROFILES_PATH = "generated"

# Backend API (pra dashboard)
API_PORT = int(os.getenv("PORT", 8080))  # Vertra usa PORT
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", '1466550471920713933')
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# Banco pra configs da dashboard (por guild)
GUILDS_DB = f"{BASE_DATA}/guilds.json"

# Config default pra guild (pra dashboard salvar)
DEFAULT_GUILD_CONFIG = {
    "prefix": "!",
    "bot_enabled": True,
    "welcome_channel": None,
    "welcome_message": "Bem-vindo {user} ao {server}!",
    "welcome_image": None,
    "tickets_category": None,
    "tickets_logs": None,
    "tickets_staff": [],
    "tickets_enabled": True,
    "autorole_time_roles": [],
    "autorole_vip": None,
    "announce_channel": None,
    "announce_interval": 48,
    "announce_message": "Anúncio padrão",
    "drops_enabled": True,
    "drops_min": 50,
    "drops_max": 500,
    "drops_chance": 1,
    "levels_enabled": True,
    "levels_xp_msg_min": 5,
    "levels_xp_msg_max": 15,
    "levels_xp_call": 2,
    "levels_roles": [],
    "economy_enabled": True,
    "economy_currency": "Fragmentos",
    "daily_enabled": True,
    "daily_reward": 250,
    "weekly_reward": 1500,
    "missions_enabled": True,
    "missions_rewards": {},
    "ranking_enabled": True,
    "ranking_global": True,
    "shop_backgrounds_enabled": True,
    "shop_colors_enabled": True,
    "presents_enabled": True,
    "social_enabled": True,
    "anonymous_enabled": True,
    "anonymous_logs": None,
    "vip_role": None,
    "vip_bonus_enabled": True
}

# cria pastas necessárias
os.makedirs(BASE_DATA, exist_ok=True)
os.makedirs(GENERATED_PROFILES_PATH, exist_ok=True)

# cria arquivos JSON automaticamente se não existirem
for path in (
    USERS_DB,
    CALLS_DB,
    SHOP_DB,
    TICKETS_DB,
    MISSOES_DB,
    GUILDS_DB  # Novo pra guilds
):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)