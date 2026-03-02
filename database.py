import json
import os
from datetime import datetime


# =========================
# LOAD JSON
# =========================

def load_json(path: str, default=None):

    if default is None:
        default = {}

    # Se o arquivo não existir, cria com valor padrão
    if not os.path.exists(path):
        save_json(path, default)
        return default.copy() if isinstance(default, dict) else default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"⚠️ JSON corrompido: {path} — recriando")
        save_json(path, default)
        return default.copy() if isinstance(default, dict) else default


# =========================
# SAVE JSON
# =========================

def save_json(path: str, data):

    folder = os.path.dirname(path)

    # Cria pasta se necessário
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# GARANTE USUÁRIO
# =========================

def ensure_user(users: dict, user_id: int):

    uid = str(user_id)

    if uid not in users:
        users[uid] = {
            # 💎 Economia
            "fragmentos": 0,
            "banco": 0,

            # 📊 Atividade
            "mensagens": 0,
            "tempo_call": 0,

            # ⭐ LEVEL SYSTEM
            "level": 0,
            "xp": 0,
            "xp_last_msg": 0,

            # 👑 VIP
            "vip_until": None,

            # 🎨 Perfil
            "background": None,
            "frame": None,
            "owned_backgrounds": [],
            "frames_owned": [],
            "items": [],
            "rank_badge": None,

            # 🎉 Eventos
            "eventos_ganhos": 0,
            "eventos_raros": 0,

            # ❤️ Social / Relacionamento
            "married_with": None,
            "marriage_date": None,
            "divorces": 0,
            "marriages": 0,
            "friends": [],

            # ⏳ COOLDOWNS
            "cooldowns": {
                "daily": None,
                "weekly": None,
                "daily_social": None
            }
        }

    base = users[uid]

    # =========================
    # SEGURANÇA PARA ATUALIZAÇÕES
    # =========================

    # Economia
    base.setdefault("fragmentos", 0)
    base.setdefault("banco", 0)

    # Atividade
    base.setdefault("mensagens", 0)
    base.setdefault("tempo_call", 0)

    # ⭐ Level
    base.setdefault("level", 0)
    base.setdefault("xp", 0)
    base.setdefault("xp_last_msg", 0)

    # VIP
    base.setdefault("vip_until", None)

    # Perfil
    base.setdefault("background", None)
    base.setdefault("frame", None)
    base.setdefault("owned_backgrounds", [])
    base.setdefault("frames_owned", [])
    base.setdefault("items", [])
    base.setdefault("rank_badge", None)

    # Eventos
    base.setdefault("eventos_ganhos", 0)
    base.setdefault("eventos_raros", 0)

    # Social
    base.setdefault("married_with", None)
    base.setdefault("marriage_date", None)
    base.setdefault("divorces", 0)
    base.setdefault("marriages", 0)
    base.setdefault("friends", [])

    # Cooldowns
    base.setdefault("cooldowns", {})
    base["cooldowns"].setdefault("daily", None)
    base["cooldowns"].setdefault("weekly", None)
    base["cooldowns"].setdefault("daily_social", None)

    return base


# =========================
# DATAS
# =========================

def now_iso():
    return datetime.utcnow().isoformat()


def iso_to_dt(iso):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None