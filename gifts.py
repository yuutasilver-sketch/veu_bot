import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from database import load_json, save_json, ensure_user
import config

GIFTS_LIST = {
    "flores": {"name": "💐 Flores", "preco": 500},
    "chocolate": {"name": "🍫 Chocolate", "preco": 800},
    "pelucia": {"name": "🧸 Pelúcia", "preco": 1500},
    "coroa": {"name": "👑 Coroa", "preco": 3000},
}


# ================= MODAL =================

class GiftModal(discord.ui.Modal):
    def __init__(self, gift_key, bot):
        super().__init__(title="Enviar Presente")
        self.gift_key = gift_key
        self.bot = bot

        self.membro = discord.ui.TextInput(
            label="Mencione o usuário",
            placeholder="@usuario",
            required=True
        )

        self.mensagem = discord.ui.TextInput(
            label="Mensagem (opcional)",
            required=False,
            max_length=200
        )

        self.add_item(self.membro)
        self.add_item(self.mensagem)

    async def on_submit(self, interaction: discord.Interaction):

        # ================= PEGAR ID DA MENÇÃO =================
        raw = self.membro.value.strip()

        if not raw.startswith("<@") or not raw.endswith(">"):
            return await interaction.response.send_message(
                "❌ Você precisa mencionar o usuário corretamente (ex: @usuario).",
                ephemeral=True
            )

        user_id = raw.replace("<@", "").replace("!", "").replace(">", "")

        try:
            membro = await self.bot.fetch_user(int(user_id))
        except:
            return await interaction.response.send_message(
                "❌ Usuário inválido.",
                ephemeral=True
            )

        if membro.bot:
            return await interaction.response.send_message(
                "❌ Não é possível enviar presentes para bots.",
                ephemeral=True
            )

        if membro.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ Você não pode enviar presente para si mesmo.",
                ephemeral=True
            )

        users = load_json(config.USERS_DB, {})
        ensure_user(users, interaction.user.id)
        ensure_user(users, membro.id)

        uid = str(interaction.user.id)
        rid = str(membro.id)

        gift_data = GIFTS_LIST[self.gift_key]
        preco = gift_data["preco"]

        if users[uid].get("fragmentos", 0) < preco:
            return await interaction.response.send_message(
                f"❌ Você não tem fragmentos suficientes. 💎 {preco} necessários.",
                ephemeral=True
            )

        users[uid]["fragmentos"] -= preco

        users[rid].setdefault("presentes_recebidos", [])
        users[rid]["presentes_recebidos"].append({
            "tipo": self.gift_key,
            "nome": gift_data["name"],
            "de": interaction.user.id,
            "mensagem": self.mensagem.value,
            "data": datetime.utcnow().timestamp()
        })

        users[uid].setdefault("presentes_enviados", [])
        users[uid]["presentes_enviados"].append({
            "tipo": self.gift_key,
            "nome": gift_data["name"],
            "para": membro.id,
            "mensagem": self.mensagem.value,
            "data": datetime.utcnow().timestamp()
        })

        users[uid].setdefault("conquistas", [])
        if len(users[uid]["presentes_enviados"]) >= 10 and "10_presentes_enviados" not in users[uid]["conquistas"]:
            users[uid]["conquistas"].append("10_presentes_enviados")

        users[rid].setdefault("conquistas", [])
        if len(users[rid]["presentes_recebidos"]) >= 10 and "10_presentes_recebidos" not in users[rid]["conquistas"]:
            users[rid]["conquistas"].append("10_presentes_recebidos")

        save_json(config.USERS_DB, users)

        embed = discord.Embed(
            title="🎁 Presente enviado!",
            description=f"{interaction.user.mention} enviou {gift_data['name']} para {membro.mention}"
                        + (f"\n💌 Mensagem: {self.mensagem.value}" if self.mensagem.value else ""),
            color=config.COLOR_PRIMARY
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= VIEW =================

class GiftView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.bot = bot

        for key, data in GIFTS_LIST.items():
            self.add_item(GiftButton(key, data, bot))


class GiftButton(discord.ui.Button):
    def __init__(self, gift_key, gift_data, bot):
        super().__init__(
            label=f"{gift_data['name']} • 💎 {gift_data['preco']}",
            style=discord.ButtonStyle.primary
        )
        self.gift_key = gift_key
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GiftModal(self.gift_key, self.bot))


# ================= COG =================

class Gifts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="presentes", description="Abrir loja de presentes")
    async def presentes(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🎁 Loja de Presentes",
            description="Escolha um presente abaixo:",
            color=config.COLOR_PRIMARY
        )

        view = GiftView(self.bot)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Gifts(bot))
