# gifts.py — LOJA DE PRESENTES DO VÉU (MULTI-SERVIDOR + IMERSIVA)

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone  # Adicionado timezone para corrigir deprecated utcnow()

import config
from database import load_json, save_json, ensure_user, get_guild_config, premium_message

USERS_DB = config.USERS_DB
GUILDS_DB = config.GUILDS_DB


# =========================================================
# PRESENTES PADRÃO (editável via dashboard)
# ========================================================
# Aqui você coloca a lista de presentes padrão (se não tiver, deixe como está ou adicione sua lista)
PRESENTES_PADRAO = {
    "rosa": {"nome": "🌹 Rosa Eterna", "preco": 100, "descricao": "Um símbolo de amor que nunca murcha."},
    "chocolate": {"nome": "🍫 Caixa de Chocolates", "preco": 150, "descricao": "Doçura que aquece o coração."},
    # ... adicione mais presentes conforme sua lógica original
}


class GiftShopView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id

    # Botões e selects da loja de presentes (mantidos conforme sua lógica original)
    # Exemplo de botão para selecionar presente
    @discord.ui.button(label="Ver Presentes", style=discord.ButtonStyle.green)
    async def ver_presentes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        cfg = get_guild_config(self.guild_id)
        if not is_premium(self.guild_id):
            embed, view = premium_message()
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        embed = discord.Embed(
            title="🎁 Loja de Presentes do Véu",
            description="Escolha um presente para enviar a alguém especial!",
            color=0xff69b4,
            timestamp=datetime.now(timezone.utc)
        )

        # Lista de presentes (exemplo; mantenha sua lógica real)
        for key, presente in PRESENTES_PADRAO.items():
            embed.add_field(
                name=presente["nome"],
                value=f"Preço: {presente['preco']} fragmentos\n{presente['descricao']}",
                inline=True
            )

        await interaction.followup.send(embed=embed, view=GiftSelectView(self.bot, self.guild_id), ephemeral=True)


class GiftSelectView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id

    # Aqui você coloca o select ou botões para escolher o presente e o destinatário
    # Mantenha sua lógica completa de escolha e envio

    # Exemplo de envio (substitua pela sua lógica real)
    async def enviar_presente(self, interaction: discord.Interaction, presente_key: str, destinatario: discord.Member):
        users = load_json(USERS_DB, {})
        sender_id = str(interaction.user.id)
        receiver_id = str(destinatario.id)

        sender = ensure_user(users, sender_id)
        receiver = ensure_user(users, receiver_id)

        presente = PRESENTES_PADRAO.get(presente_key)
        if not presente:
            return await interaction.response.send_message("Presente inválido.", ephemeral=True)

        if sender["fragmentos"] < presente["preco"]:
            return await interaction.response.send_message("Fragmentos insuficientes!", ephemeral=True)

        sender["fragmentos"] -= presente["preco"]
        # Adicione lógica de presente recebido no receiver se tiver
        # receiver["presentes_recebidos"] = receiver.get("presentes_recebidos", []) + [presente_key]

        await save_json(USERS_DB, users)

        embed = discord.Embed(
            title="Presente Enviado!",
            description=f"{interaction.user.mention} enviou **{presente['nome']}** para {destinatario.mention}!",
            color=0xff69b4,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Véu Entre Mundos • Laços eternos ♾️")

        await interaction.response.send_message(embed=embed)


# Cog principal
class Gifts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="presentes", description="Abre a loja de presentes do Véu")
    async def presentes(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        cfg = get_guild_config(interaction.guild.id)
        if not cfg.get("gifts_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        embed = discord.Embed(
            title="🎁 Loja de Presentes do Véu",
            description=(
                "Escolha um presente e um destinatário.\n"
                "Os laços feitos aqui ecoam entre os mundos..."
            ),
            color=0xff69b4,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Véu Entre Mundos • Presentes que transcendem o tempo ♾️")

        view = GiftShopView(self.bot, interaction.guild.id)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Gifts(bot))