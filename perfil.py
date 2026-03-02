import os
import io
import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from PIL import Image, ImageDraw, ImageFont

import config
from database import load_json, save_json, ensure_user


# =========================
# CONFIG
# =========================
USERS_DB = config.USERS_DB
SHOP_DB = config.SHOP_DB
GEN_PATH = config.GENERATED_PROFILES_PATH

os.makedirs(GEN_PATH, exist_ok=True)

AUTO_UPDATE_INTERVAL = 10

PROFILE_TASKS = {}
PROFILE_CACHE = {}


# =========================
# XP
# =========================
def xp_needed(level: int):
    XP_BASE = 120
    XP_MULT = 1.18
    return int(XP_BASE * (XP_MULT ** level))


# =========================
# FONT SAFE
# =========================
def font(size):
    for path in (
        "assets/font.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "arial.ttf",
    ):
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()


# =========================
# UTILS
# =========================
def format_time(sec):
    sec = int(sec or 0)
    h = sec // 3600
    m = (sec % 3600) // 60
    return f"{h}h {m}m"


def vip_days(data):
    try:
        dt = datetime.fromisoformat(data.get("vip_until"))
        r = (dt - datetime.utcnow()).days
        return r if r > 0 else 0
    except:
        return 0


def convert_progress(data):
    return data.get("mensagens", 0) // 100, data.get("tempo_call", 0) // 600


# =========================
# RESOLVERS
# =========================
def resolve_bg(data):
    shop = load_json(SHOP_DB, {})
    bg = data.get("background")

    if not bg:
        owned = data.get("owned_backgrounds", [])
        if owned:
            bg = owned[0]

    item = shop.get(bg)

    if item and os.path.exists(item.get("file", "")):
        return item["file"]

    return config.DEFAULT_PROFILE_BACKGROUND


def resolve_frame(data):
    shop = load_json(SHOP_DB, {})
    fr = data.get("frame")

    if not fr:
        owned = data.get("owned_frames") or data.get("frames_owned") or []
        if owned:
            fr = owned[0]

    item = shop.get(fr)

    if item and os.path.exists(item.get("file", "")):
        return item["file"]

    return None


# =========================
# GERAR PERFIL
# =========================
async def gerar(member, data):

    # =========================
    # CAMPOS SOCIAIS (SOMENTE LEITURA)
    # =========================
    data.setdefault("friends", [])
    data.setdefault("married_to", None)

    cache_key = (
        member.id,
        data.get("fragmentos"),
        data.get("banco"),
        data.get("mensagens"),
        data.get("tempo_call"),
        data.get("background"),
        data.get("frame"),
        vip_days(data),
        data.get("level", 0),
        data.get("xp", 0),
        len(data.get("friends", [])),
        data.get("married_to"),
    )

    if cache_key in PROFILE_CACHE:
        return PROFILE_CACHE[cache_key]

    bg = Image.open(resolve_bg(data)).convert("RGBA").resize((1000, 500))
    overlay = Image.new("RGBA", (1000, 500), (10, 5, 25, 220))
    base = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(base)

    card = Image.new("RGBA", (900, 420), (25, 15, 45, 240))
    base.paste(card, (50, 40), card)

    av = await member.display_avatar.replace(size=512).read()
    avatar = Image.open(io.BytesIO(av)).convert("RGBA").resize((220, 220))

    mask = Image.new("L", (220, 220), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)

    base.paste(avatar, (390, 120), mask)

    frame = resolve_frame(data)
    if frame:
        f = Image.open(frame).convert("RGBA").resize((260, 260))
        base.paste(f, (370, 100), f)

    draw.text((500, 70), "✦ PERFIL DO GUARDIÃO ✦",
              anchor="mm", font=font(34), fill=(255, 210, 160))

    draw.text((500, 105), member.name,
              anchor="mm", font=font(30), fill=(255, 255, 255))

    level = data.get("level", 0)
    xp = data.get("xp", 0)
    needed = xp_needed(level)

    left_x = 140
    right_x = 700
    y = 200

    left_stats = [
        f"Fragmentos: {data.get('fragmentos', 0)}",
        f"Banco: {data.get('banco', 0)}",
        f"Nível: {level}",
        f"Amigos: {len(data.get('friends', []))}",
    ]

    right_stats = [
        f"Mensagens: {data.get('mensagens', 0)}",
        f"Call: {format_time(data.get('tempo_call', 0))}",
    ]

    for t in left_stats:
        draw.text((left_x, y), t, font=font(24), fill=(230, 230, 230))
        y += 45

    y = 200

    for t in right_stats:
        draw.text((right_x, y), t, font=font(24), fill=(230, 230, 230))
        y += 45

    # CASAMENTO (APENAS EXIBIÇÃO)
    married_id = data.get("married_to")
    if married_id:
        partner = member.guild.get_member(married_id)
        nome = partner.name if partner else "Desconhecido"
        draw.text(
            (500, 300),
            f"💍 Casado com: {nome}",
            anchor="mm",
            font=font(24),
            fill=(255, 180, 200),
        )

    draw.text(
        (500, 350),
        f"XP: {xp} / {needed}",
        anchor="mm",
        font=font(22),
        fill=(200, 200, 255),
    )

    bar_x1 = 200
    bar_x2 = 800
    bar_y1 = 380
    bar_y2 = 400

    draw.rounded_rectangle((bar_x1, bar_y1, bar_x2, bar_y2),
                           radius=12, fill=(40, 40, 70))

    progress = xp / needed if needed > 0 else 0
    fill_x = bar_x1 + int((bar_x2 - bar_x1) * progress)

    draw.rounded_rectangle((bar_x1, bar_y1, fill_x, bar_y2),
                           radius=12, fill=(170, 90, 255))

    vip = vip_days(data)
    if vip > 0:
        draw.text(
            (500, 420),
            f"⭐ VIP {vip} dias restantes",
            anchor="mm",
            font=font(20),
            fill=(255, 210, 120),
        )

    path = f"{GEN_PATH}/{member.id}.png"
    base.save(path)

    PROFILE_CACHE[cache_key] = path
    return path

# =========================
# AUTO UPDATE
# =========================
async def auto_update(message, user):
    try:
        while True:
            users = load_json(USERS_DB, {})
            data = ensure_user(users, user.id)

            path = await gerar(user, data)

            await message.edit(
                file=discord.File(path),
                view=PerfilView(user),
            )

            await asyncio.sleep(AUTO_UPDATE_INTERVAL)

    except (discord.NotFound, discord.Forbidden):
        pass
    finally:
        PROFILE_TASKS.pop(user.id, None)

# =========================
# EDITAR FUNDOS / MOLDURAS
# =========================
class EditarPerfilView(discord.ui.View):
    def __init__(self, user, message, tipo="background", index=0):
        super().__init__(timeout=None)
        self.user = user
        self.message = message
        self.tipo = tipo
        self.index = index

        users = load_json(USERS_DB, {})
        self.data = ensure_user(users, user.id)

        if tipo == "background":
            self.itens = self.data.get("owned_backgrounds", [])
        else:
            self.itens = self.data.get("owned_frames") or self.data.get("frames_owned") or []

        self.shop = load_json(SHOP_DB, {})

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "❌ Apenas o dono do perfil pode usar isso.",
                ephemeral=True,
            )
            return False
        return True

    def nome_item(self):
        if not self.itens:
            return "Nenhum item"
        return self.shop.get(self.itens[self.index], {}).get("name", self.itens[self.index])

    async def atualizar_msg(self, interaction):
        await interaction.response.edit_message(
            content=f"Visualizando: **{self.nome_item()}**",
            view=self,
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction, _):
        if not self.itens:
            return
        self.index = (self.index - 1) % len(self.itens)
        await self.atualizar_msg(interaction)

    @discord.ui.button(label="✅ Equipar", style=discord.ButtonStyle.success)
    async def equipar(self, interaction, _):

        if not self.itens:
            return await interaction.response.send_message(
                "❌ Você não possui itens.",
                ephemeral=True,
            )

        users = load_json(USERS_DB, {})
        d = ensure_user(users, self.user.id)

        if self.tipo == "background":
            d["background"] = self.itens[self.index]
        else:
            d["frame"] = self.itens[self.index]

        save_json(USERS_DB, users)

        PROFILE_CACHE.clear()

        if self.user.id in PROFILE_TASKS:
            PROFILE_TASKS[self.user.id].cancel()

        path = await gerar(self.user, d)

        await interaction.response.edit_message(
            content=f"✅ **{self.nome_item()} equipado!**",
            view=self,
        )

        await self.message.edit(
            file=discord.File(path),
            view=PerfilView(self.user),
        )

        PROFILE_TASKS[self.user.id] = asyncio.create_task(
            auto_update(self.message, self.user)
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction, _):
        if not self.itens:
            return
        self.index = (self.index + 1) % len(self.itens)
        await self.atualizar_msg(interaction)


# =========================
# MODAL BANCO
# =========================
class QuantidadeModal(discord.ui.Modal):
    quantidade = discord.ui.TextInput(label="Quantidade", required=True)

    def __init__(self, acao, message):
        super().__init__(title="Informe a quantidade")
        self.acao = acao
        self.message = message

    async def on_submit(self, interaction):

        try:
            qtd = int(self.quantidade.value)
            if qtd <= 0:
                raise ValueError
        except:
            return await interaction.response.send_message(
                "Quantidade inválida.",
                ephemeral=True,
            )

        users = load_json(USERS_DB, {})
        d = ensure_user(users, interaction.user.id)

        if self.acao == "depositar":
            if d["fragmentos"] < qtd:
                return await interaction.response.send_message(
                    "Fragmentos insuficientes.",
                    ephemeral=True,
                )
            d["fragmentos"] -= qtd
            d["banco"] += qtd
        else:
            if d["banco"] < qtd:
                return await interaction.response.send_message(
                    "Saldo insuficiente.",
                    ephemeral=True,
                )
            d["banco"] -= qtd
            d["fragmentos"] += qtd

        save_json(USERS_DB, users)

        path = await gerar(interaction.user, d)

        await interaction.response.send_message(
            "✅ Operação realizada.",
            ephemeral=True,
        )

        await self.message.edit(
            file=discord.File(path),
            view=PerfilView(interaction.user),
        )


# =========================
# VIEW PRINCIPAL
# =========================
class PerfilView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "❌ Você não pode mexer no perfil de outra pessoa.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="🔄 Converter", style=discord.ButtonStyle.blurple)
    async def conv(self, interaction, _):
        users = load_json(USERS_DB, {})
        d = ensure_user(users, interaction.user.id)

        m, c = convert_progress(d)
        total = m + c

        if total <= 0:
            return await interaction.response.send_message(
                "Nada para converter.",
                ephemeral=True,
            )

        d["mensagens"] = max(0, d.get("mensagens", 0) - m * 100)
        d["tempo_call"] = max(0, d.get("tempo_call", 0) - c * 600)
        d["fragmentos"] += total

        save_json(USERS_DB, users)
        PROFILE_CACHE.clear()

        path = await gerar(interaction.user, d)

        await interaction.message.edit(
            file=discord.File(path),
            view=PerfilView(interaction.user),
        )

        await interaction.response.send_message(
            f"+{total} Fragmentos",
            ephemeral=True,
        )

    @discord.ui.button(label="💰 Depositar", style=discord.ButtonStyle.green)
    async def dep(self, interaction, _):
        await interaction.response.send_modal(
            QuantidadeModal("depositar", interaction.message)
        )

    @discord.ui.button(label="🏧 Sacar", style=discord.ButtonStyle.gray)
    async def sac(self, interaction, _):
        await interaction.response.send_modal(
            QuantidadeModal("sacar", interaction.message)
        )

    @discord.ui.button(label="🖼️ Fundos", style=discord.ButtonStyle.secondary)
    async def fundos(self, interaction, _):
        await interaction.response.send_message(
            "Visualizando fundos:",
            view=EditarPerfilView(self.user, interaction.message, "background"),
            ephemeral=True,
        )

    @discord.ui.button(label="🖼️ Molduras", style=discord.ButtonStyle.secondary)
    async def molduras(self, interaction, _):
        await interaction.response.send_message(
            "Visualizando molduras:",
            view=EditarPerfilView(self.user, interaction.message, "frame"),
            ephemeral=True,
        )


# =========================
# COG
# =========================
class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil")
    async def perfil(self, interaction, membro: discord.Member = None):
        await interaction.response.defer(thinking=True)

        membro = membro or interaction.user

        if membro.id in PROFILE_TASKS:
            PROFILE_TASKS[membro.id].cancel()

        users = load_json(USERS_DB, {})
        data = ensure_user(users, membro.id)

        path = await gerar(membro, data)
        msg = await interaction.followup.send(file=discord.File(path))
        await msg.edit(view=PerfilView(membro))

        PROFILE_TASKS[membro.id] = asyncio.create_task(
            auto_update(msg, membro)
        )


async def setup(bot):
    await bot.add_cog(Perfil(bot))