import discord
from discord.ext import commands
from discord import app_commands

from database import load_json, save_json, ensure_user
import config

USERS_DB = config.USERS_DB

MARRIAGE_COST = 500
DIVORCE_COST = 300


# =========================
# GARANTIR CAMPOS SOCIAIS
# =========================
def ensure_social(data: dict):
    data.setdefault("friends", [])
    data.setdefault("married_to", None)
    data.setdefault("status_social", "Disponível")
    data.setdefault("humor", "Neutro")
    data.setdefault("reputacao", 0)
    return data


# =========================
# MENU SOCIAL
# =========================
class SocialMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot

    @discord.ui.button(label="🤝 Amizade", style=discord.ButtonStyle.primary)
    async def amizade_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use /amizade @usuario", ephemeral=True)

    @discord.ui.button(label="💍 Casar", style=discord.ButtonStyle.success)
    async def casar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"Use /relacionamento @usuario\n💰 Custo: {MARRIAGE_COST} fragmentos",
            ephemeral=True
        )

    @discord.ui.button(label="💔 Divorciar", style=discord.ButtonStyle.danger)
    async def divorcio_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"Use /terminar\n💰 Custo: {DIVORCE_COST} fragmentos",
            ephemeral=True
        )

    @discord.ui.button(label="🌟 Reputar", style=discord.ButtonStyle.secondary)
    async def reputar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use /reputar @usuario", ephemeral=True)


# =========================
# COG
# =========================
class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # MENU
    # =========================
    @app_commands.command(name="social")
    async def social_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💞 Sistema Social",
            description="Gerencie amizades, relacionamentos e reputação.",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, view=SocialMenu(self.bot))

    # =========================
    # AMIZADE
    # =========================
    @app_commands.command(name="amizade")
    async def amizade(self, interaction: discord.Interaction, membro: discord.Member):

        if membro.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode adicionar a si mesmo.", ephemeral=True)

        users = load_json(USERS_DB, {})
        autor = ensure_user(users, interaction.user.id)
        alvo = ensure_user(users, membro.id)

        ensure_social(autor)
        ensure_social(alvo)

        if membro.id in autor["friends"]:
            return await interaction.response.send_message("❌ Já são amigos.", ephemeral=True)

        autor["friends"].append(membro.id)
        alvo["friends"].append(interaction.user.id)

        save_json(USERS_DB, users)

        await interaction.response.send_message(f"🤝 Agora você e {membro.mention} são amigos!")

    # =========================
    # CASAMENTO COM TAXA (FRAGMENTOS)
    # =========================
    @app_commands.command(name="relacionamento")
    async def relacionamento(self, interaction: discord.Interaction, membro: discord.Member):

        if membro.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode casar consigo mesmo.", ephemeral=True)

        users = load_json(USERS_DB, {})
        autor = ensure_user(users, interaction.user.id)
        alvo = ensure_user(users, membro.id)

        ensure_social(autor)
        ensure_social(alvo)

        if autor["married_to"]:
            return await interaction.response.send_message("❌ Você já está casado.", ephemeral=True)

        if alvo["married_to"]:
            return await interaction.response.send_message("❌ Essa pessoa já está casada.", ephemeral=True)

        if autor["fragmentos"] < MARRIAGE_COST:
            return await interaction.response.send_message(
                f"❌ Você precisa de {MARRIAGE_COST} fragmentos para casar.",
                ephemeral=True
            )

        class Pedido(discord.ui.View):
            @discord.ui.button(label="💖 Aceitar", style=discord.ButtonStyle.success)
            async def aceitar(self, i: discord.Interaction, button: discord.ui.Button):

                if i.user.id != membro.id:
                    return await i.response.send_message("❌ Apenas o alvo pode aceitar.", ephemeral=True)

                autor["fragmentos"] -= MARRIAGE_COST
                autor["married_to"] = membro.id
                alvo["married_to"] = interaction.user.id

                save_json(USERS_DB, users)

                await i.response.edit_message(content="💍 Casamento realizado com sucesso!", view=None)

            @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
            async def recusar(self, i: discord.Interaction, button: discord.ui.Button):
                await i.response.edit_message(content="💔 Pedido recusado.", view=None)

        await interaction.response.send_message(
            f"{membro.mention}, aceita casar com {interaction.user.mention}?\n💰 Custo: {MARRIAGE_COST} fragmentos",
            view=Pedido()
        )

    # =========================
    # DIVÓRCIO COM TAXA (FRAGMENTOS)
    # =========================
    @app_commands.command(name="terminar")
    async def terminar(self, interaction: discord.Interaction):

        users = load_json(USERS_DB, {})
        user = ensure_user(users, interaction.user.id)

        ensure_social(user)

        if not user["married_to"]:
            return await interaction.response.send_message("❌ Você não está casado.", ephemeral=True)

        if user["fragmentos"] < DIVORCE_COST:
            return await interaction.response.send_message(
                f"❌ Você precisa de {DIVORCE_COST} fragmentos para divorciar.",
                ephemeral=True
            )

        parceiro = ensure_user(users, user["married_to"])
        ensure_social(parceiro)

        user["fragmentos"] -= DIVORCE_COST
        parceiro["married_to"] = None
        user["married_to"] = None

        save_json(USERS_DB, users)

        await interaction.response.send_message("💔 Divórcio realizado com sucesso.")

    # =========================
    # REPUTAÇÃO
    # =========================
    @app_commands.command(name="reputar")
    async def reputar(self, interaction: discord.Interaction, membro: discord.Member):

        if membro.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode se reputar.", ephemeral=True)

        users = load_json(USERS_DB, {})
        alvo = ensure_user(users, membro.id)

        ensure_social(alvo)

        alvo["reputacao"] += 1

        save_json(USERS_DB, users)

        await interaction.response.send_message(f"🌟 {membro.mention} recebeu +1 reputação!")


async def setup(bot):
    await bot.add_cog(Social(bot))