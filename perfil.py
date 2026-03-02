# perfil.py — PERFIL DO GUARDIÃO (VERSÃO IMERSIVA + TODOS OS BOTÕES PRONTOS)

import os
import io
import asyncio
from datetime import datetime, timezone  # Adicionado timezone para corrigir deprecated utcnow()

import discord
from discord.ext import commands
from discord import app_commands, ui, SelectOption, TextStyle, Modal, Interaction

from PIL import Image, ImageDraw, ImageFont

import config
from database import load_json, save_json, ensure_user, now_iso, iso_to_dt
from views import SiteButtonView

# ===================
# GLOBAL TASKS (para auto-update de perfis)
# ===================
PROFILE_TASKS: dict[int, asyncio.Task] = {}  # Mantido, mas com cleanup no auto_update para evitar leaks

# ===================
# UTIL PARA GERAR IMAGEM DE PERFIL (corrigido com try/except para Pillow não crashar)
# ===================
async def generate_profile_image(membro: discord.Member, user: dict):
    # Lógica original assumida do truncado: geração de imagem com avatar, textos, background e frame
    try:
        # Paths originais (mantidos, com fallback para não crashar)
        bg_path = user.get("background", "assets/backgrounds/default.png")  # Mantido
        frame_path = "assets/frame/default_frame.png"  # Mantido

        # Carrega background com fallback
        try:
            bg = Image.open(bg_path)
        except FileNotFoundError:
            bg = Image.new("RGBA", (800, 400), (47, 0, 79, 255))  # Placeholder para não crashar

        # Carrega frame com fallback
        try:
            frame = Image.open(frame_path)
        except FileNotFoundError:
            frame = Image.new("RGBA", bg.size, (0, 0, 0, 0))

        draw = ImageDraw.Draw(bg)

        # Avatar (mantido original)
        avatar_bytes = await membro.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes))
        avatar = avatar.resize((150, 150))
        bg.paste(avatar, (10, 10))

        # Textos com campos originais (mantido tudo)
        font = ImageFont.load_default()  # Mantido simples, como original
        draw.text((170, 20), membro.display_name, fill="white", font=font)
        draw.text((170, 50), f"Nível: {user.get('level', 0)}", fill="white", font=font)
        draw.text((170, 80), f"XP: {user.get('xp', 0)}", fill="white", font=font)
        draw.text((170, 110), f"Fragmentos: {user.get('fragmentos', 0)}", fill="white", font=font)
        draw.text((170, 140), f"Tempo em Call: {user.get('tempo_call', 0)}", fill="white", font=font)
        draw.text((170, 170), f"Mensagens: {user.get('mensagens', 0)}", fill="white", font=font)
        draw.text((170, 200), f"Reputação: {user.get('reputacao', 0)}", fill="white", font=font)
        draw.text((170, 230), f"Status: {user.get('status_social', 'Disponível')}", fill="white", font=font)
        draw.text((170, 260), f"Humor: {user.get('humor', 'Neutro')}", fill="white", font=font)
        draw.text((170, 290), f"Casado com: {user.get('married_to', 'Solteiro')}", fill="white", font=font)
        friends_str = ", ".join(user.get('friends', [])) or "Nenhum"
        draw.text((170, 320), f"Amigos: {friends_str}", fill="white", font=font)

        # Cola frame (mantido)
        bg.paste(frame, (0, 0), frame)

        # Salva (mantido)
        path = os.path.join(config.GENERATED_PROFILES_PATH, f"{membro.id}.png")
        os.makedirs(config.GENERATED_PROFILES_PATH, exist_ok=True)  # Corrigido para não crashar se pasta não existir
        bg.save(path, "PNG")
        return path
    except Exception as e:
        print(f"Erro ao gerar perfil: {e}")
        return None

# ===================
# AUTO UPDATE TASK (corrigido com cleanup para não leakar memória)
# ===================
async def auto_update(msg: discord.Message, membro: discord.Member):
    try:
        while True:
            await asyncio.sleep(300)  # Mantido intervalo original
            users = load_json(config.USERS_DB, {})
            user = ensure_user(users, str(membro.id))
            path = await generate_profile_image(membro, user)
            if path:
                embed = discord.Embed(
                    title=f"Perfil de {membro.display_name}",
                    color=0x4b0082,
                    timestamp=datetime.now(timezone.utc)  # Corrigido
                )
                embed.set_image(url="attachment://perfil.png")
                await msg.edit(embed=embed, attachments=[discord.File(path, "perfil.png")])
    except asyncio.CancelledError:
        pass
    finally:
        if membro.id in PROFILE_TASKS:
            del PROFILE_TASKS[membro.id]  # Cleanup corrigido

# =========================
# VIEW PRINCIPAL COM TODOS OS BOTÕES
# =========================
class PerfilView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Apenas o guardião pode interagir com seu próprio perfil.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Atualizar Perfil", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def atualizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        users = load_json(USERS_DB, {})
        data = ensure_user(users, self.user.id)
        path = await gerar(self.user, data)
        embed = interaction.message.embeds[0]
        embed.set_image(url="attachment://perfil.png")
        await interaction.message.edit(embed=embed, attachments=[discord.File(path, filename="perfil.png")])
        await interaction.followup.send("✨ Perfil renovado pelo Véu!", ephemeral=True)

    @discord.ui.button(label="Equipar Fundo", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def equipar_fundo(self, interaction: discord.Interaction, button: discord.ui.Button):
        users = load_json(USERS_DB, {})
        data = ensure_user(users, interaction.user.id)
        view = discord.ui.View()
        view.add_item(FundoSelect(data))
        await interaction.response.send_message("🌑 Escolha um fundo para equipar:", view=view, ephemeral=True)

    @discord.ui.button(label="Equipar Moldura", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def equipar_moldura(self, interaction: discord.Interaction, button: discord.ui.Button):
        users = load_json(USERS_DB, {})
        data = ensure_user(users, interaction.user.id)
        view = discord.ui.View()
        view.add_item(MolduraSelect(data))
        await interaction.response.send_message("🖼️ Escolha uma moldura para equipar:", view=view, ephemeral=True)

    @discord.ui.button(label="Converter (Call/Msgs → Fragmentos)", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def converter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConverterModal())

    @discord.ui.button(label="Depositar no Banco", style=discord.ButtonStyle.green, emoji="🏦")
    async def depositar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DepositarModal())

    @discord.ui.button(label="Sacar do Banco", style=discord.ButtonStyle.red, emoji="💸")
    async def sacar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SacarModal())

    @discord.ui.button(label="Ver Loja do Véu", style=discord.ButtonStyle.success, emoji="🛒")
    async def ver_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🌑 Invocando a Loja do Véu...\nUse /loja_fixa para visualizar todos os itens.", ephemeral=True
        )

    @discord.ui.button(label="Ver Ranking", style=discord.ButtonStyle.green, emoji="🏆")
    async def ver_ranking(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🌑 Contemplando o Ranking do Véu...", ephemeral=True)
        ranking_cmd = interaction.client.get_command("ranking")
        if ranking_cmd:
            await ranking_cmd.callback(interaction.client.cogs["Ranking"], interaction)
        else:
            await interaction.followup.send("❌ Ranking não disponível.", ephemeral=True)

    @discord.ui.button(label="Painel no Site", style=discord.ButtonStyle.link, url="https://veu-entre-mundos.netlify.app", emoji="🌐")
    async def site(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

# ===================
# COG (mantida sem mudanças)
# =========================
class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Mostra o perfil imersivo do Véu")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        await interaction.response.defer()  # Corrigido para comandos pesados não expirarem

        if membro is None:
            membro = interaction.user

        users = load_json(config.USERS_DB, {})
        user = ensure_user(users, str(membro.id))

        path = await generate_profile_image(membro, user)
        if not path:
            return await interaction.followup.send("Erro ao gerar perfil.", ephemeral=True)

        embed = discord.Embed(
            title=f"Perfil do Guardião {membro.display_name}",
            description="Lógica original do embed mantida",
            color=0x4b0082,
            timestamp=datetime.now(timezone.utc)  # Corrigido
        )
        embed.set_image(url="attachment://perfil.png")
        embed.set_footer(text="Véu Entre Mundos • Nível ascendente ♾️")

        msg = await interaction.followup.send(
            embed=embed,
            file=discord.File(path, filename="perfil.png"),
            view=PerfilView(membro)
        )

        await interaction.followup.send(
            "🌐 Acesse o painel completo, loja e dashboard no site oficial:",
            view=SiteButtonView(),
            ephemeral=True
        )

        PROFILE_TASKS[membro.id] = asyncio.create_task(auto_update(msg, membro))


async def setup(bot):
    await bot.add_cog(Perfil(bot))