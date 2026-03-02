# anonymous.py — SISTEMA ANÔNIMO CONFIDENCIAL (ENVIO NO PRIVADO)

import discord
from discord.ext import commands
from discord import app_commands
from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message, now_iso, iso_to_dt
import config
from datetime import datetime, timedelta

COOLDOWN_SECONDS = 120  # 2 minutos para evitar spam

class AnonModal(discord.ui.Modal, title="Mensagem Confidencial"):
    mensagem = discord.ui.TextInput(
        label="Escreva sua mensagem",
        style=discord.TextStyle.paragraph,
        placeholder="Aqui ninguém vai saber que foi você... seja sincero.",
        required=True,
        max_length=2000
    )

    def __init__(self, tipo: str, bot, interaction: discord.Interaction):
        super().__init__()
        self.tipo = tipo
        self.bot = bot
        self.interaction = interaction  # Guardamos para usar no on_submit

    async def on_submit(self, interaction: discord.Interaction):
        mensagem = self.mensagem.value.strip()
        if not mensagem:
            return await interaction.response.send_message("Não pode enviar vazio.", ephemeral=True)

        agora = datetime.utcnow()

        # Embed que vai ser enviado no PRIVADO do usuário
        embed_privado = discord.Embed(
            title=f"🕯️ Sua {self.tipo.capitalize()} Anônima",
            description=mensagem,
            color=0x4b0082,
            timestamp=agora
        )
        embed_privado.set_footer(text="Véu Entre Mundos • Isso é só entre você e o Véu ♾️")

        try:
            await self.interaction.user.send(embed=embed_privado)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não consegui enviar no seu privado. Ative as DMs do servidor ou do bot.",
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro ao enviar: {str(e)}",
                ephemeral=True
            )
            return

        # Log no canal configurado (com autor real)
        cfg = get_guild_config(self.interaction.guild.id)
        log_id = cfg.get("anonymous_logs")
        log_channel = self.interaction.guild.get_channel(log_id)
        if log_channel:
            log_embed = discord.Embed(
                title=f"Log de {self.tipo.capitalize()} Anônima (Enviada no Privado)",
                description=(
                    f"**Autor:** {self.interaction.user} ({self.interaction.user.id})\n"
                    f"**Mensagem:** {mensagem}\n"
                    f"**Enviada para:** {self.interaction.user.mention} (DM)"
                ),
                color=0x95a5a6,
                timestamp=agora
            )
            log_embed.set_thumbnail(url=self.interaction.user.display_avatar.url)
            await log_channel.send(embed=log_embed)

        # Atualiza cooldown
        uid = str(self.interaction.user.id)
        users = load_json(config.USERS_DB, {})
        user = ensure_user(users, uid)
        user["cooldowns"]["anon_last"] = now_iso()
        save_json(config.USERS_DB, users)

        await interaction.response.send_message(
            f"✅ Sua {self.tipo} foi enviada **no seu privado** com sucesso.\nNinguém mais viu.",
            ephemeral=True
        )


class AnonView(discord.ui.View):
    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.bot = bot
        self.interaction = interaction

    @discord.ui.button(label="Confissão", style=discord.ButtonStyle.secondary, emoji="🖤")
    async def confissao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnonModal("confissão", self.bot, self.interaction))

    @discord.ui.button(label="Elogio", style=discord.ButtonStyle.success, emoji="✨")
    async def elogio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnonModal("elogio", self.bot, self.interaction))

    @discord.ui.button(label="Desabafo", style=discord.ButtonStyle.danger, emoji="💔")
    async def desabafo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnonModal("desabafo", self.bot, self.interaction))

    @discord.ui.button(label="Conselho", style=discord.ButtonStyle.primary, emoji="🧠")
    async def conselho(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnonModal("conselho", self.bot, self.interaction))


class Anonymous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anon_confissao", description="Abra o painel confidencial para enviar mensagem só para você mesmo")
    async def anon_panel(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("anonymous_enabled", False):
            return await interaction.response.send_message("❌ Sistema de mensagens confidenciais está desativado.", ephemeral=True)

        if not is_premium(guild_id):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        # Cooldown check
        uid = str(interaction.user.id)
        users = load_json(config.USERS_DB, {})
        user = ensure_user(users, uid)
        last_iso = user.get("cooldowns", {}).get("anon_last")
        ultimo = iso_to_dt(last_iso)

        agora = datetime.utcnow()
        if ultimo and (agora - ultimo).total_seconds() < COOLDOWN_SECONDS:
            restante = COOLDOWN_SECONDS - int((agora - ultimo).total_seconds())
            minutos = restante // 60
            segundos = restante % 60
            return await interaction.response.send_message(
                f"⏳ Aguarde {minutos}m {segundos}s para abrir outro painel confidencial.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🕯️ Mensagem Confidencial Só Para Você",
            description=(
                "Aqui você pode desabafar, confessar, elogiar a si mesmo ou pedir conselho...\n"
                "Tudo será enviado **direto no seu privado**.\n"
                "Ninguém no servidor vai ver. Só você e o Véu."
            ),
            color=0x4b0082
        )
        embed.set_footer(text="Véu Entre Mundos • Seu segredo está seguro ♾️")

        view = AnonView(self.bot, interaction)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Anonymous(bot))