import discord
from discord import app_commands
from discord.ext import commands
import io
from PIL import Image, ImageDraw

from database import load_json, save_json, ensure_user
import config

USERS_DB = config.USERS_DB
SHOP_DB = config.SHOP_DB

BG_PATH = "assets/backgrounds"
FRAME_PATH = "assets/frame"

PREVIEW_CACHE: dict[str, bytes] = {}

# ==================================================
# ================= SHOP PADRÃO ====================
# ==================================================

DEFAULT_SHOP = {

    # ================= FUNDOS =================

    "bg_lua": {
        "type": "background",
        "name": "Lua Arcana",
        "price": 12000,
        "file": f"{BG_PATH}/lua.png",
        "desc": "Luz lunar do Véu",
        "rarity": "COMUM"
    },

    "bg_void": {
        "type": "background",
        "name": "Vazio Entre Mundos",
        "price": 18000,
        "file": f"{BG_PATH}/void.png",
        "desc": "Energia cósmica instável",
        "rarity": "RARO"
    },

    "bg_abismo": {
        "type": "background",
        "name": "Abismo Antigo",
        "price": 32000,
        "file": f"{BG_PATH}/abismo.png",
        "desc": "O eco das profundezas",
        "rarity": "ÉPICO"
    },

    "bg_fragmento": {
        "type": "background",
        "name": "Fragmento Primordial",
        "price": 26000,
        "file": f"{BG_PATH}/fragmento.png",
        "desc": "Eco de outra realidade",
        "rarity": "RARO"
    },

    "bg_portal": {
        "type": "background",
        "name": "Portal Entre Mundos",
        "price": 38000,
        "file": f"{BG_PATH}/portal.png",
        "desc": "A fronteira dos mundos",
        "rarity": "LENDÁRIO"
    },

    "bg_caverna_dragao": {
        "type": "background",
        "name": "Caverna do Dragão",
        "price": 30000,
        "file": f"{BG_PATH}/caverna_dodragao.png",
        "desc": "O lar das feras ancestrais",
        "rarity": "ÉPICO"
    },

    "bg_nevoa": {
        "type": "background",
        "name": "Névoa do Véu",
        "price": 20000,
        "file": f"{BG_PATH}/nevoa.png",
        "desc": "Nada é o que parece",
        "rarity": "RARO"
    },

    "bg_oceano": {
        "type": "background",
        "name": "Oceano Profundo",
        "price": 24000,
        "file": f"{BG_PATH}/oceano.png",
        "desc": "As águas misteriosas do Véu",
        "rarity": "RARO"
    },

    "bg_mar_rosas": {
        "type": "background",
        "name": "Mar de Rosas",
        "price": 28000,
        "file": f"{BG_PATH}/mar_rosas.png",
        "desc": "Um oceano florido carmesim",
        "rarity": "ÉPICO"
    },

    "bg_infernal": {
        "type": "background",
        "name": "Infernal",
        "price": 18000,
        "file": f"{BG_PATH}/infernal.png",
        "desc": "Os confins do Inferno",
        "rarity": "RARO"
    },

    # ================= MOLDURAS =================

    "frame_rosas": {
        "type": "frame",
        "name": "Moldura Rosas Carmesim",
        "price": 90000,
        "file": f"{FRAME_PATH}/frame_rosa.png",
        "desc": "Rosas vivas do Véu",
        "rarity": "LENDÁRIO"
    },

    "frame_void": {
        "type": "frame",
        "name": "Moldura Void",
        "price": 75000,
        "file": f"{FRAME_PATH}/frame_void.png",
        "desc": "Energia distorcida",
        "rarity": "ÉPICO"
    },

    "frame_cogumelos": {
        "type": "frame",
        "name": "Moldura Cogumelos",
        "price": 82000,
        "file": f"{FRAME_PATH}/frame_cogumelos.png",
        "desc": "Estilhaços cósmicos",
        "rarity": "RARO"
    },

    "frame_dragao_veu": {
        "type": "frame",
        "name": "Moldura Dragão do Véu",
        "price": 250000,
        "file": f"{FRAME_PATH}/frame_dragao_veu.png",
        "desc": "Concedida aos guardiões do Véu",
        "rarity": "MITICA"
    },

    "frame_olhares": {
        "type": "frame",
        "name": "Moldura Crystal",
        "price": 68000,
        "file": f"{FRAME_PATH}/frame_crystal.png",
        "desc": "Os Cristais mais puros do Véu",
        "rarity": "RARO"
    },

    "frame_polvo": {
        "type": "frame",
        "name": "Moldura Polvo Abissal",
        "price": 72000,
        "file": f"{FRAME_PATH}/frame_polvo.png",
        "desc": "Criatura das profundezas",
        "rarity": "ÉPICO"
    },

    "frame_infernal": {
        "type": "frame",
        "name": "Moldura Infernal",
        "price": 110000,
        "file": f"{FRAME_PATH}/frame_infernal.png",
        "desc": "Chamas eternas do abismo",
        "rarity": "LENDÁRIO"
    },

    "frame_floresta": {
        "type": "frame",
        "name": "Moldura da Floresta",
        "price": 85000,
        "file": f"{FRAME_PATH}/frame_floresta.png",
        "desc": "Raízes vivas e energia natural",
        "rarity": "ÉPICO"
    },

    "frame_tecnologica": {
        "type": "frame",
        "name": "Moldura Tecnológica do Véu",
        "price": 140000,
        "file": f"{FRAME_PATH}/frame_tecnologica.png",
        "desc": "Circuitos arcanos avançados",
        "rarity": "MITICA"
    },
}

# ==================================================
# ================= LOAD SHOP ======================
# ==================================================

def ensure_shop():
    data = load_json(SHOP_DB, {})
    if not data:
        save_json(SHOP_DB, DEFAULT_SHOP)
        return DEFAULT_SHOP

    for k, v in DEFAULT_SHOP.items():
        data.setdefault(k, v)

    save_json(SHOP_DB, data)
    return data

# ==================================================
# ================= PREVIEW ========================
# ==================================================

async def gerar_preview(item, user: discord.User):

    size = 380
    avatar_bytes = await user.display_avatar.replace(size=512).read()
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((300, 300))

    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 300, 300), fill=255)

    avatar_round = Image.new("RGBA", (300, 300))
    avatar_round.paste(avatar, (0, 0), mask)

    base = Image.new("RGBA", (size, size), (20, 20, 20, 255))
    base.paste(avatar_round, (40, 40), avatar_round)

    if item["type"] == "background":
        base = Image.open(item["file"]).convert("RGBA").resize((size, size))

    if item["type"] == "frame":
        frame = Image.open(item["file"]).convert("RGBA").resize((size, size))
        base.paste(frame, (0, 0), frame)

    buf = io.BytesIO()
    base.save(buf, "PNG")
    buf.seek(0)

    return discord.File(buf, filename="preview.png")

# ==================================================
# ================= VIEW ===========================
# ==================================================

class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.shop = ensure_shop()
        self.categoria = "background"
        self.page = 0
        self.update_items()

    def update_items(self):
        self.items = [(k, v) for k, v in self.shop.items() if v["type"] == self.categoria]
        self.page = 0

    def get_item(self):
        return self.items[self.page]

    async def build(self, interaction):
        item_id, item = self.get_item()

        embed = discord.Embed(
            title=f"{item['name']} • {item['rarity']}",
            description=item["desc"],
            color=config.COLOR_PRIMARY
        )

        embed.add_field(
            name="Preço",
            value=f"{item['price']} {config.CURRENCY_NAME}"
        )

        embed.set_footer(
            text=f"{self.page + 1}/{len(self.items)} • {'Fundos' if self.categoria=='background' else 'Molduras'}"
        )

        file = await gerar_preview(item, interaction.user)
        embed.set_image(url="attachment://preview.png")

        return embed, file

    @discord.ui.button(label="🎨 Fundos", style=discord.ButtonStyle.blurple, row=0, custom_id="loja_fundos")
    async def fundos(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.categoria = "background"
        self.update_items()
        embed, file = await self.build(interaction)
        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

    @discord.ui.button(label="🖼️ Molduras", style=discord.ButtonStyle.secondary, row=0, custom_id="loja_molduras")
    async def molduras(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.categoria = "frame"
        self.update_items()
        embed, file = await self.build(interaction)
        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray, row=1, custom_id="loja_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = (self.page - 1) % len(self.items)
        embed, file = await self.build(interaction)
        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray, row=1, custom_id="loja_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = (self.page + 1) % len(self.items)
        embed, file = await self.build(interaction)
        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

    @discord.ui.button(label="🛒 Comprar", style=discord.ButtonStyle.green, row=2, custom_id="loja_comprar")
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):

        users = load_json(USERS_DB, {})
        data = ensure_user(users, interaction.user.id)

        item_id, item = self.get_item()

        if data.get("fragmentos", 0) < item["price"]:
            return await interaction.response.send_message("❌ Fragmentos insuficientes.", ephemeral=True)

        if item["type"] == "background":
            data.setdefault("owned_backgrounds", [])
            if item_id in data["owned_backgrounds"]:
                return await interaction.response.send_message("⚠️ Você já possui esse fundo.", ephemeral=True)
            data["owned_backgrounds"].append(item_id)
        else:
            data.setdefault("frames_owned", [])
            if item_id in data["frames_owned"]:
                return await interaction.response.send_message("⚠️ Você já possui essa moldura.", ephemeral=True)
            data["frames_owned"].append(item_id)

        data["fragmentos"] -= item["price"]
        save_json(USERS_DB, users)

        await interaction.response.send_message("✅ Item comprado com sucesso!", ephemeral=True)

# ==================================================
# ================= COG ============================
# ==================================================

class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja_fixa", description="Envia a loja fixa no canal (somente ADM)")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_fixa(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        view = LojaView()
        embed, file = await view.build(interaction)

        await interaction.channel.send(embed=embed, view=view, file=file)
        await interaction.followup.send("✅ Loja fixa enviada neste canal.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Loja(bot))