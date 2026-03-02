# ranking.py

import discord
from discord import app_commands
from discord.ext import commands

from PIL import Image, ImageDraw, ImageFont
import io
import os

import config
from database import load_json

USERS_DB = config.USERS_DB
MISSOES_DB = config.MISSOES_DB

RANKING_BG = "assets/ranking_bg.png"


# =========================
# UTIL
# =========================

def sort_users(users: dict, key: str):
    return sorted(
        users.items(),
        key=lambda x: x[1].get(key, 0),
        reverse=True
    )


def sort_missoes(missoes: dict):
    ranking = []

    for uid, data in missoes.items():
        total = 0
        for nome in ["mensagens", "evento", "evento_raro", "fragmentos", "call", "semanal"]:
            if nome in data and data[nome].get("concluida"):
                total += 1
        ranking.append((uid, total))

    return sorted(ranking, key=lambda x: x[1], reverse=True)


def format_call(seconds: int):
    seconds = int(seconds or 0)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def cut_name(text, limit=20):
    return text if len(text) <= limit else text[:limit] + "..."


def draw_text_outline(draw, pos, text, font, fill):
    x, y = pos
    for dx in (-2, -1, 1, 2):
        for dy in (-2, -1, 1, 2):
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text(pos, text, font=font, fill=fill)


def tipo_label(tipo):
    labels = {
        "fragmentos": "Fragmentos",
        "mensagens": "Mensagens",
        "tempo_call": "Tempo em Call",
        "eventos_ganhos": "Eventos Ganhos",
        "eventos_raros": "Eventos Raros",
        "missoes": "Missões Concluídas",

        # 🔥 NOVOS
        "reputacao": "Reputação",
        "popularidade": "Popularidade",
        "interacoes": "Interações",
        "presentes_enviados": "Presentes Enviados",
        "presentes_recebidos": "Presentes Recebidos",
        "streak_daily": "Streak Daily",
        "banco": "Banco",
    }
    return labels.get(tipo, "Valor")


def make_circle_avatar(img: Image.Image, size=64):
    img = img.resize((size, size)).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    avatar = Image.new("RGBA", (size, size))
    avatar.paste(img, (0, 0), mask)

    return avatar


# =========================
# GERAR IMAGEM DE UMA PÁGINA
# =========================

async def generate_rank_image(interaction, ordered, tipo, page):

    start = page * 10
    data = ordered[start:start + 10]

    W, H = 1100, 720

    if os.path.exists(RANKING_BG):
        base = Image.open(RANKING_BG).convert("RGBA").resize((W, H))
    else:
        base = Image.new("RGBA", (W, H), (25, 15, 35, 255))

    draw = ImageDraw.Draw(base)

    font_title = load_font(60)
    font_name = load_font(36)
    font_value = load_font(34)

    title_text = f"RANKING — {tipo_label(tipo).upper()}"
    tw = draw.textlength(title_text, font=font_title)

    draw_text_outline(draw, ((W - tw) // 2, 28), title_text, font_title, (255, 200, 120))

    y = 130
    medals = ["🥇", "🥈", "🥉"]

    for i, entry in enumerate(data):
        pos = start + i + 1

        if tipo == "missoes":
            uid, value = entry
        else:
            uid, user_data = entry
            value = user_data.get(tipo, 0)

        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        name = f"@{member.name}" if member else f"@ID{uid}"
        name = cut_name(name)

        if tipo == "tempo_call":
            value = format_call(value)

        draw.rounded_rectangle(
            (120, y - 10, W - 120, y + 68),
            radius=18,
            fill=(45, 30, 70, 215)
        )

        medal = medals[pos - 1] if pos <= 3 else f"#{pos}"

        # avatar
        if member:
            avatar_bytes = await member.display_avatar.replace(size=128).read()
            avatar_img = Image.open(io.BytesIO(avatar_bytes))
            avatar_circle = make_circle_avatar(avatar_img, 64)
            base.paste(avatar_circle, (140, y - 4), avatar_circle)

        draw_text_outline(draw, (220, y + 6), f"{medal} {name}", font_name, (255, 255, 255))

        value_text = str(value)
        vw = draw.textlength(value_text, font=font_value)

        draw_text_outline(draw, (W - 160 - vw, y + 16), value_text, font_value, (120, 180, 255))

        y += 80

    buffer = io.BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)

    return discord.File(buffer, filename="rank.png")


# =========================
# VIEW DE PAGINAÇÃO
# =========================

class RankView(discord.ui.View):

    def __init__(self, interaction, ordered, tipo):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.ordered = ordered
        self.tipo = tipo
        self.page = 0
        self.max_page = (len(ordered) - 1) // 10

    async def update(self, interaction):
        file = await generate_rank_image(self.interaction, self.ordered, self.tipo, self.page)

        embed = discord.Embed(
            title=f"📊 Ranking — Página {self.page + 1}/{self.max_page + 1}",
            color=config.COLOR_PRIMARY
        )
        embed.set_image(url="attachment://rank.png")

        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("❌ Apenas quem executou pode usar.", ephemeral=True)

        if self.page > 0:
            self.page -= 1

        await self.update(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("❌ Apenas quem executou pode usar.", ephemeral=True)

        if self.page < self.max_page:
            self.page += 1

        await self.update(interaction)


# =========================
# COG
# =========================

class Ranking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rank", description="Ranking visual do servidor")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Fragmentos", value="fragmentos"),
        app_commands.Choice(name="Mensagens", value="mensagens"),
        app_commands.Choice(name="Tempo em Call", value="tempo_call"),
        app_commands.Choice(name="Eventos Pegos", value="eventos_ganhos"),
        app_commands.Choice(name="Eventos Raros", value="eventos_raros"),
        app_commands.Choice(name="Missões Concluídas", value="missoes"),

        # 🔥 NOVOS
        app_commands.Choice(name="Reputação", value="reputacao"),
        app_commands.Choice(name="Popularidade", value="popularidade"),
        app_commands.Choice(name="Interações", value="interacoes"),
        app_commands.Choice(name="Presentes Enviados", value="presentes_enviados"),
        app_commands.Choice(name="Presentes Recebidos", value="presentes_recebidos"),
        app_commands.Choice(name="Streak Daily", value="streak_daily"),
        app_commands.Choice(name="Banco", value="banco"),
    ])
    async def rank(self, interaction: discord.Interaction, tipo: app_commands.Choice[str]):

        await interaction.response.defer(thinking=True)

        users = load_json(USERS_DB, {})
        missoes = load_json(MISSOES_DB, {})

        if tipo.value == "missoes":
            ordered = sort_missoes(missoes)[:50]
        else:
            ordered = sort_users(users, tipo.value)[:50]

        if not ordered:
            return await interaction.followup.send("❌ Sem dados suficientes.")

        view = RankView(interaction, ordered, tipo.value)

        file = await generate_rank_image(interaction, ordered, tipo.value, 0)

        embed = discord.Embed(
            title="📊 Ranking Visual",
            color=config.COLOR_PRIMARY
        )
        embed.set_image(url="attachment://rank.png")

        await interaction.followup.send(embed=embed, file=file, view=view)


async def setup(bot):
    await bot.add_cog(Ranking(bot))