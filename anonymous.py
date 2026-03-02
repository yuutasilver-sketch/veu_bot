import discord
from discord.ext import commands
from discord import app_commands
from database import load_json, save_json, ensure_user
import config
from datetime import datetime, timedelta

# =========================
# Controle de cooldowns
# =========================
COOLDOWN_SECONDS = 60  # 1 minuto entre envios anônimos

class Anonymous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message = {}  # UID -> timestamp do último envio

    # =========================
    # /anon_confissao
    # =========================
    @app_commands.command(name="anon_confissao", description="Envie uma confissão anônima para outro usuário")
    @app_commands.describe(destinatario="Membro que vai receber a confissão", mensagem="Sua confissão anônima")
    async def confissao(self, interaction: discord.Interaction, destinatario: discord.Member, mensagem: str):
        await self.send_anonymous(interaction, destinatario, mensagem, tipo="Confissão")

    # =========================
    # /anon_pergunta
    # =========================
    @app_commands.command(name="anon_pergunta", description="Envie uma pergunta anônima para outro usuário")
    @app_commands.describe(destinatario="Membro que vai receber a pergunta", pergunta="Sua pergunta anônima")
    async def pergunta(self, interaction: discord.Interaction, destinatario: discord.Member, pergunta: str):
        await self.send_anonymous(interaction, destinatario, pergunta, tipo="Pergunta")

    # =========================
    # /anon_avaliacao
    # =========================
    @app_commands.command(name="anon_avaliacao", description="Envie uma avaliação anônima para outro usuário")
    @app_commands.describe(destinatario="Membro que vai receber a avaliação", avaliacao="Sua avaliação anônima")
    async def avaliacao(self, interaction: discord.Interaction, destinatario: discord.Member, avaliacao: str):
        await self.send_anonymous(interaction, destinatario, avaliacao, tipo="Avaliação")

    # =========================
    # Função genérica de envio anônimo
    # =========================
    async def send_anonymous(self, interaction: discord.Interaction, destinatario: discord.Member, mensagem: str, tipo: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        uid = str(interaction.user.id)
        agora = datetime.utcnow()

        # Verifica cooldown
        if uid in self.last_message:
            diff = (agora - self.last_message[uid]).total_seconds()
            if diff < COOLDOWN_SECONDS:
                restante = int(COOLDOWN_SECONDS - diff)
                return await interaction.followup.send(f"⏳ Aguarde {restante}s antes de enviar outra mensagem anônima.")

        self.last_message[uid] = agora

        # =========================
        # Embed da mensagem anônima
        # =========================
        embed = discord.Embed(
            title=f"🕵️ {tipo} Anônima Recebida",
            description=mensagem,
            color=config.COLOR_PRIMARY,
            timestamp=agora
        )
        embed.set_footer(text="Véu Entre Mundos • Mensagem Anônima")

        try:
            await destinatario.send(embed=embed)
        except discord.Forbidden:
            return await interaction.followup.send("❌ Não consegui enviar DM para esse usuário.")

        # =========================
        # Log opcional
        # =========================
        canal_log_id = getattr(config, "ANONYMOUS_LOG_CHANNEL_ID", None)
        if canal_log_id:
            canal_log = self.bot.get_channel(canal_log_id)
            if canal_log:
                log_embed = discord.Embed(
                    title="📜 Log de Mensagem Anônima",
                    description=f"Tipo: {tipo}\nDe: {interaction.user} ({interaction.user.id})\nPara: {destinatario} ({destinatario.id})",
                    color=0x95a5a6,
                    timestamp=agora
                )
                await canal_log.send(embed=log_embed)

        await interaction.followup.send(f"✅ Sua {tipo.lower()} foi enviada com sucesso para {destinatario.display_name}!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Anonymous(bot))