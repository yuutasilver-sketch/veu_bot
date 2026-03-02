# database.py — MULTI-SERVIDOR + PREMIUM CHECK + VIP COM FALLBACK DE CARGO

import json
import os
from datetime import datetime, timezone
import asyncio

import config

SAVE_LOCK = asyncio.Lock()

def load_json(path: str, default=None):
    if default is None:
        default = {}

    if not os.path.exists(path):
        save_json(path, default)
        return default.copy() if isinstance(default, dict) else default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"JSON corrompido em {path}. Usando default.")
        return default.copy() if isinstance(default, dict) else default
    except Exception as e:
        print(f"Erro ao carregar JSON {path}: {e}")
        return default.copy() if isinstance(default, dict) else default

async def save_json(path: str, data):
    async with SAVE_LOCK:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar JSON {path}: {e}")

def ensure_user(data: dict, uid: str):
    if uid not in data:
        data[uid] = {
            "fragmentos": 0,
            "cooldowns": {},
            "vip_ativo": False,
            "vip_expira": None,
            "xp": 0,
            "level": 0,
            "mensagens": 0,
            "tempo_call": 0,
            "missoes": {},
            "friends": [],
            "married_to": None,
            "status_social": "Disponível",
            "humor": "Neutro",
            "reputacao": 0,
            "last_marriage": None,
            "background": "",
            "moldura": "",
            "banco": 0,
        }
    return data[uid]

def ensure_guild(data: dict, guild_id: str):
    if guild_id not in data:
        data[guild_id] = config.DEFAULT_GUILD_CONFIG.copy()
    return data[guild_id]

def get_guild_config(guild_id: int | str):
    guilds = load_json(config.GUILDS_DB, {})
    gid = str(guild_id)
    return ensure_guild(guilds, gid)

def get_guild_plan(guild_id: int | str) -> str:
    cfg = get_guild_config(guild_id)
    return cfg.get("plan", "free")

def is_premium(guild_id: int | str) -> bool:
    return get_guild_plan(guild_id) == "premium"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def iso_to_dt(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    except Exception:
        return None

def vip_days(user_data: dict) -> int:
    expire_iso = user_data.get("vip_expira")
    if not expire_iso:
        return 0
    expire_dt = iso_to_dt(expire_iso)
    if not expire_dt:
        return 0
    delta = expire_dt - datetime.now(timezone.utc)
    return max(delta.days, 0)

def is_vip(user_data: dict, member=None) -> bool:
    if user_data.get("vip_ativo", False):
        expire = iso_to_dt(user_data.get("vip_expira"))
        if expire and datetime.now(timezone.utc) < expire:
            return True

    if member is not None:
        guild_id = str(member.guild.id)
        guilds_data = load_json(config.GUILDS_DB, {})
        guild_cfg = ensure_guild(guilds_data, guild_id)
        vip_role_id = guild_cfg.get("vip_role_id")
        if vip_role_id:
            try:
                vip_role = member.guild.get_role(int(vip_role_id))
                if vip_role and vip_role in member.roles:
                    return True
            except Exception as e:
                print(f"Erro ao checar cargo VIP: {e}")
    return False