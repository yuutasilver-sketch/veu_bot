# config.py — VÉU MULTI-SERVIDOR + SITE READY

import os
import json

# ─────────────────────────────
# BOT
# ─────────────────────────────

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN não encontrado")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

OWNER_ID = 551080982493528106

# ─────────────────────────────
# LINKS (IMPORTANTE)
# ─────────────────────────────

BACKEND_URL = "https://random-a5failmc8869f.vertraweb.app"
SITE_URL = "https://veu-entre-mundos.netlify.app"

REDIRECT_URI = f"{SITE_URL}/callback.html"

# ─────────────────────────────
# CORES PADRÃO
# ─────────────────────────────

COLOR_PRIMARY = 0x8A2BE2
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xF1C40F
COLOR_INFO = 0x3498DB

# ─────────────────────────────
# ECONOMIA
# ─────────────────────────────

CURRENCY_NAME = "Fragmentos"
CURRENCY_EMOJI = "💎"
DAILY_REWARD = 500
WEEKLY_REWARD = 3500

# ─────────────────────────────
# PASTAS E DBs
# ─────────────────────────────

BASE_DATA = "database"
USERS_DB = os.path.join(BASE_DATA, "users.json")
CALLS_DB = os.path.join(BASE_DATA, "calls.json")
SHOP_DB = os.path.join(BASE_DATA, "shop.json")
TICKETS_DB = os.path.join(BASE_DATA, "tickets.json")
MISSOES_DB = os.path.join(BASE_DATA, "missoes.json")
GUILDS_DB = os.path.join(BASE_DATA, "guilds.json")

GENERATED_PROFILES_PATH = os.path.join("generated", "profiles")

# ─────────────────────────────
# DEFAULT GUILD CONFIG
# ─────────────────────────────

DEFAULT_GUILD_CONFIG = {
    "bot_enabled": True,
    "prefix": "!",
    "levels_enabled": True,
    "levels_xp_min": 15,
    "levels_xp_max": 25,
    "levels_announce_channel": None,
    "drops_enabled": True,
    "drops_chance": 0.5,
    "drops_min": 50,
    "drops_max": 200,
    "ranking_enabled": True,
    "color_shop_enabled": True,
    "vip_enabled": True,
    "vip_discount": 0.20,
    "vip_price": 1_000_000,
    "vip_duration_days": 30,
    "announce_enabled": False,
    "announce_channel": None,
    "announce_message": "Bem-vindo ao Véu!",
    "announce_interval_hours": 24,
    "last_announce": None,
    "tickets_enabled": True,
    "tickets_panel_canal": None,
    "tickets_panel_text": "Abra um ticket!",
    "tickets_panel_image": None,
    "tickets_buttons": [],
    "tickets_category": None,
    "autorole_time_roles": [],
    "autorole_vip": None,
    "shop_enabled": True,
    "shop_colors_enabled": True,
    "presents_enabled": True,
    "social_enabled": True,
    "anonymous_enabled": True,
    "anonymous_logs": None,
    "vip_role": None,
    "vip_bonus_enabled": True,
    "plan": "free"
}

# ─────────────────────────────
# CRIAÇÃO AUTOMÁTICA DE PASTAS
# ─────────────────────────────

os.makedirs(BASE_DATA, exist_ok=True)
os.makedirs(GENERATED_PROFILES_PATH, exist_ok=True)

for path in (
    USERS_DB, CALLS_DB, SHOP_DB, TICKETS_DB, MISSOES_DB, GUILDS_DB
):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
