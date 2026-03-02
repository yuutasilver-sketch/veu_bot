# loja.py — LOJA DO VÉU (MULTI-SERVIDOR + DASHBOARD INTEGRADA + IMERSIVA)

import discord
from discord import app_commands
from discord.ext import commands
import io
from PIL import Image, ImageDraw

from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message
import config

USERS_DB = config.USERS_DB
SHOP_DB = config.SHOP_DB

BG_PATH = "assets/backgrounds"
FRAME_PATH = "assets/frame"

PREVIEW_CACHE: dict[str, bytes] = {}


# ==================================================
# ================= SHOP PADRÃO (EXPANDIDA) ====================
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
# UTIL PARA PREVIEW
# ==================================================
async def generate_preview(item_id, item):
    if item_id in PREVIEW_CACHE:
        return PREVIEW_CACHE[item_id]

    if item["type"] == "background":
        img = Image.open(item["file"]).resize((300, 150))
    elif item["type"] == "frame":
        img = Image.open(item["file"]).resize((150, 150))
    else:
        return None

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    PREVIEW_CACHE[item_id] = buffer.read()
    return discord.File(io.BytesIO(PREVIEW_CACHE[item_id]), filename="preview.png")


# ==================================================
# VIEW PARA LOJA (PERSISTENTE + BOTÕES FUNCIONAIS)
# ==================================================
class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def build(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("shop_enabled", True):
            embed, view = premium_message()
            return embed, None, view

        shop = cfg.get("shop_items", DEFAULT_SHOP)

        embed = discord.Embed(
            title="🛒 Loja Eterna do Véu",
            description=(
                "Bem-vindo à loja onde os fragmentos eternos compram relíquias místicas.\n"
                "Escolha categorias abaixo e troque seus fragmentos por fundos, molduras e mais!\n\n"
                "💎 Moeda: Fragmentos\n"
                "👑 VIP: Descontos exclusivos"
            ),
            color=0x4b0082,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Véu Entre Mundos • Compre e transforme sua jornada ♾️")

        # Botões para categorias (mais visuais)
        button_fundos = discord.ui.Button(label="Fundos Místicos", style=discord.ButtonStyle.primary, emoji="🌌")
        button_fundos.callback = self.ver_fundos
        self.add_item(button_fundos)

        button_molduras = discord.ui.Button(label="Molduras Eternas", style=discord.ButtonStyle.primary, emoji="🖼️")
        button_molduras.callback = self.ver_molduras
        self.add_item(button_molduras)

        return embed, None


    async def ver_fundos(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)
        shop = cfg.get("shop_items", DEFAULT_SHOP)
        fundos = {k: v for k, v in shop.items() if v["type"] == "background"}

        embed = discord.Embed(
            title="🌌 Fundos Místicos do Véu",
            description="Escolha um fundo para personalizar seu perfil eterno.",
            color=0x4b0082
        )

        for k, v in fundos.items():
            embed.add_field(
                name=f"{v['name']} — {v['price']:,} 💎",
                value=v['descricao'],
                inline=False
            )

        view = CompraView("background", fundos, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    async def ver_molduras(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)
        shop = cfg.get("shop_items", DEFAULT_SHOP)
        molduras = {k: v for k, v in shop.items() if v["type"] == "frame"}

        embed = discord.Embed(
            title="🖼️ Molduras Eternas do Véu",
            description="Escolha uma moldura para enquadrar sua alma.",
            color=0x4b0082
        )

        for k, v in molduras.items():
            embed.add_field(
                name=f"{v['name']} — {v['price']:,} 💎",
                value=v['descricao'],
                inline=False
            )

        view = CompraView("frame", molduras, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==================================================
# VIEW PARA COMPRA (COM PREVIEW E CONFIRMAÇÃO)
# ==================================================
class CompraView(discord.ui.View):
    def __init__(self, tipo, itens, user_id):
        super().__init__(timeout=300)
        self.tipo = tipo
        self.itens = itens
        self.user_id = user_id

    @discord.ui.button(label="Comprar Item", style=discord.ButtonStyle.success, emoji="💎")
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Apenas você pode comprar em sua loja.", ephemeral=True)

        options = [SelectOption(label=v["name"], value=k) for k, v in self.itens.items()]

        select = ui.Select(placeholder="Selecione o item para comprar...", options=options)
        select.callback = self.confirmar_compra

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message("🌑 Escolha o item a comprar:", view=view, ephemeral=True)

    async def confirmar_compra(self, interaction: discord.Interaction):
        item_id = interaction.data["values"][0]
        item = self.itens[item_id]
        price = item["price"]
        users = load_json(USERS_DB, {})
        user = ensure_user(users, self.user_id)

        is_vip = vip_days(user) > 0
        final_price = int(price * 0.8) if is_vip else price  # 20% off VIP

        if user["fragmentos"] < final_price:
            return await interaction.response.send_message(f"❌ Fragmentos insuficientes. Precisa de {final_price:,} 💎.", ephemeral=True)

        # Preview
        file = await generate_preview(item_id, item)

        embed = discord.Embed(
            title=f"🌑 Confirmar Compra: {item['name']}",
            description=f"{item['descricao']}\nPreço: {final_price:,} 💎{' (desconto VIP 20%)' if is_vip else ''}",
            color=0x4b0082
        )
        embed.set_image(url="attachment://preview.png")

        class ConfirmarView(discord.ui.View):
            @discord.ui.button(label="Confirmar Compra", style=discord.ButtonStyle.success)
            async def confirmar(self, inter: discord.Interaction, btn: discord.ui.Button):
                user["fragmentos"] -= final_price
                if self.tipo == "background":
                    user.setdefault("owned_backgrounds", []).append(item_id)
                elif self.tipo == "frame":
                    user.setdefault("owned_frames", []).append(item_id)
                save_json(USERS_DB, users)
                await inter.response.send_message(f"✨ {item['name']} adquirido! Equipado automaticamente.", ephemeral=True)

            @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
            async def cancelar(self, inter: discord.Interaction, btn: discord.ui.Button):
                await inter.response.send_message("Compra cancelada.", ephemeral=True)

        await interaction.response.send_message(embed=embed, file=file, view=ConfirmarView(), ephemeral=True)


# =========================================================
# COG LOJA
# =========================================================
class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja_fixa", description="Invoca a loja fixa no canal (somente ADM)")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_fixa(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("shop_enabled", True):
            embed, view = premium_message()
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        view = LojaView()
        embed, _ = await view.build(interaction)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.followup.send("✅ Loja do Véu invocada neste canal.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Loja(bot))