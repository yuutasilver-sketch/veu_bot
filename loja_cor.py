# loja_cor.py — LOJA DE CORES DO VÉU (MULTI-SERVIDOR + IMERSIVA)

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message
import config


USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB


# =========================================================
# CONFIG PADRÃO (fallback + MUITAS CORES NOVAS)
# =========================================================

DEFAULT_CONFIG = {
    "color_shop_enabled": True,
    "vip_enabled": True,
    "vip_discount": 0.20,
    "vip_price": 1_000_000,
    "vip_duration_days": 30,
    "color_base_role": None,
    "colors": {
        # Cores clássicas (mantidas)
        "Violeta do Véu": {"price": 1500, "hex": 0x8e44ad, "descricao": "Um violeta profundo como o Véu noturno."},
        "Azul Abissal": {"price": 1200, "hex": 0x1f3a93, "descricao": "Azul das profundezas eternas."},
        "Rosa Arcano": {"price": 1800, "hex": 0xff69b4, "descricao": "Rosa místico de segredos arcano."},
        "Verde Esmeralda": {"price": 1400, "hex": 0x50c878, "descricao": "Verde de florestas encantadas."},
        "Dourado Eterno": {"price": 2500, "hex": 0xffd700, "descricao": "Dourado reluzente do Véu dourado."},

        # Novas cores adicionadas (mais 15+ para variedade)
        "Vermelho Carmesim": {"price": 1600, "hex": 0xdc143c, "descricao": "Vermelho intenso como sangue dos mundos caídos."},
        "Preto Vazio": {"price": 1000, "hex": 0x000000, "descricao": "Preto absoluto que absorve toda luz."},
        "Branco Lunar": {"price": 1100, "hex": 0xffffff, "descricao": "Branco puro da luz da lua eterna."},
        "Laranja Flamejante": {"price": 1300, "hex": 0xff4500, "descricao": "Laranja das chamas que nunca se apagam."},
        "Ciano Oceânico": {"price": 1700, "hex": 0x00ffff, "descricao": "Ciano das águas abissais do Véu."},
        "Amarelo Solar": {"price": 1900, "hex": 0xffff00, "descricao": "Amarelo brilhante como sóis distantes."},
        "Magenta Místico": {"price": 2100, "hex": 0xff00ff, "descricao": "Magenta de magias antigas e proibidas."},
        "Cinza Sombrio": {"price": 900, "hex": 0x808080, "descricao": "Cinza das sombras esquecidas."},
        "Turquesa Arcana": {"price": 2000, "hex": 0x40e0d0, "descricao": "Turquesa de portais arcanos."},
        "Marrom Terreno": {"price": 800, "hex": 0x8b4513, "descricao": "Marrom das terras antigas do Véu."},
        "Indigo Profundo": {"price": 2200, "hex": 0x4b0082, "descricao": "Índigo das profundezas do Véu."},
        "Prata Estelar": {"price": 2300, "hex": 0xc0c0c0, "descricao": "Prata que reflete estrelas perdidas."},
        "Verde Venenoso": {"price": 1450, "hex": 0x00ff00, "descricao": "Verde tóxico das poções proibidas."},
        "Roxo Imperial": {"price": 2400, "hex": 0x9932cc, "descricao": "Roxo da realeza entre mundos."},
        "Azul Elétrico": {"price": 1750, "hex": 0x00bfff, "descricao": "Azul elétrico das tempestades cósmicas."},
        "Marfim Antigo": {"price": 950, "hex": 0xfffff0, "descricao": "Marfim das relíquias esquecidas."},
        "Bronze Ancestral": {"price": 1050, "hex": 0xcd7f32, "descricao": "Bronze das civilizações perdidas."},
        "Pêssego Suave": {"price": 850, "hex": 0xffdab9, "descricao": "Pêssego suave como amanhecer no Véu."},
        "Lavanda Noturna": {"price": 1350, "hex": 0xe6e6fa, "descricao": "Lavanda que floresce sob a lua."},
        "Safira Profunda": {"price": 2600, "hex": 0x0f52ba, "descricao": "Safira das joias do abismo."}
    }
}


# =========================================================
# UTIL PARA DESCONTO VIP
# =========================================================
def calc_preco(price, is_vip):
    return int(price * (1 - DEFAULT_CONFIG["vip_discount"]) if is_vip else price)


# =========================================================
# VIEW PARA LOJA DE CORES (PERSISTENTE + BOTÕES)
# =========================================================
class LojaCorView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="Comprar Cor", style=discord.ButtonStyle.success, emoji="🎨")
    async def comprar_cor(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_guild_config(self.guild_id)
        colors = cfg.get("colors", DEFAULT_CONFIG["colors"])

        options = [SelectOption(label=nome, value=nome, description=f"{dados['price']} 💎") for nome, dados in colors.items()]

        select = ui.Select(placeholder="Selecione uma cor mística...", options=options)
        select.callback = self.confirmar_cor

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message("🌑 Escolha uma cor para tingir sua alma:", view=view, ephemeral=True)

    async def confirmar_cor(self, interaction: discord.Interaction):
        nome = interaction.data["values"][0]
        cfg = get_guild_config(self.guild_id)
        dados = cfg.get("colors", DEFAULT_CONFIG["colors"]).get(nome)

        users = load_json(USERS_DB, {})
        user = ensure_user(users, interaction.user.id)
        is_vip = vip_days(user) > 0
        price = calc_preco(dados["price"], is_vip)

        if user["fragmentos"] < price:
            return await interaction.response.send_message(f"❌ Fragmentos insuficientes. Precisa de {price} 💎.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎨 Confirmar Cor: {nome}",
            description=f"{dados['descricao']}\nPreço: {price} 💎{' (desconto VIP)' if is_vip else ''}",
            color=dados["hex"]
        )

        class ConfirmarCorView(discord.ui.View):
            @discord.ui.button(label="Confirmar Compra", style=discord.ButtonStyle.success)
            async def confirmar(self, inter: discord.Interaction, btn: discord.ui.Button):
                user["fragmentos"] -= price
                user.setdefault("owned_colors", []).append(nome)
                user["cor"] = nome  # Equipa automaticamente
                save_json(USERS_DB, users)
                await inter.response.send_message(f"✨ Cor **{nome}** adquirida e equipada!", ephemeral=True)

            @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger)
            async def cancelar(self, inter: discord.Interaction, btn: discord.ui.Button):
                await inter.response.send_message("Compra cancelada.", ephemeral=True)

        await interaction.response.send_message(embed=embed, view=ConfirmarCorView(), ephemeral=True)


# =========================================================
# COG LOJA COR
# =========================================================
class LojaCor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja_cor", description="Invoca a loja de cores no canal (ADM apenas)")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_cor(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("color_shop_enabled", True):
            embed, view = premium_message()
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        colors = cfg.get("colors", DEFAULT_CONFIG["colors"])

        descricao = "Escolha sua cor personalizada no Véu.\n\n"

        for nome, dados in colors.items():
            descricao += f"🎨 **{nome}** — {dados['price']} 💎\n{dados['descricao']}\n"

        descricao += "\n👑 VIP recebe desconto\n🎭 Apenas uma cor ativa por alma"

        embed = discord.Embed(
            title="🎨 Loja de Cores Eternas do Véu",
            description=descricao,
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Véu Entre Mundos • Tingir sua jornada ♾️")

        await interaction.channel.send(embed=embed, view=LojaCorView(guild_id))
        await interaction.followup.send("✅ Loja de Cores invocada neste canal.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(LojaCor(bot))
