import discord
from discord.ext import commands
from discord import app_commands
import config


# =========================
# COG AJUDA — VÉU
# =========================

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # =========================
    # /ajuda
    # =========================
    @app_commands.command(
        name="ajuda",
        description="Mostra todos os comandos da Véu"
    )
    async def ajuda(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📜 CENTRAL DE COMANDOS — VÉU",
            description=(
                "Aqui estão todos os comandos disponíveis da **Véu Entre Mundos**.\n"
                "Use com sabedoria… o Véu observa 🕯️"
            ),
            color=config.COLOR_PRIMARY
        )

        # 🎫 Tickets
        embed.add_field(
            name="🎫 Tickets & Suporte",
            value=(
                "`/ticket_painel` → Abrir painel de tickets (ADM)\n"
                "`/fechar_ticket` → Fechar ticket (Staff)"
            ),
            inline=False
        )

        # 💰 Economia
        embed.add_field(
            name="💰 Economia & Perfil",
            value=(
                "`/perfil` → Ver seu perfil\n"
                "`/daily` → Recompensa diária\n"
                "`/weekly` → Recompensa semanal\n"
                "`/daily_social` → Bônus social\n"
                "`/enviar` → Enviar fragmentos para alguém\n"
                "`/apostar` → Apostar fragmentos"
            ),
            inline=False
        )

        # 🎯 Missões & Eventos
        embed.add_field(
            name="🎯 Missões & Eventos",
            value=(
                "`/missoes` → Ver missões disponíveis\n"
                "`/resgatar_missoes` → Resgatar recompensas\n"
                "`/proximo_evento` → Tempo para próximo evento"
            ),
            inline=False
        )

        # 🛒 Loja
        embed.add_field(
            name="🛒 Loja & Customização",
            value=(
                "`/loja_fixa` → Enviar loja fixa (ADM)\n"
                "`/loja_cor_fixa` → Enviar loja de cores (ADM)"
            ),
            inline=False
        )

        # 📊 Ranking
        embed.add_field(
            name="📊 Ranking",
            value=(
                "`/rank` → Ver ranking do servidor\n"
                "`/top_fragmentos` → Top economia (se existir)"
            ),
            inline=False
        )

        # 🛠️ Administração
        embed.add_field(
            name="🛠️ Administração (Staff)",
            value=(
                "`/add_fragmentos` → Adicionar fragmentos (ADM)\n"
                "`/remover_fragmentos` → Remover fragmentos (ADM)\n"
                "`/resetar_usuario` → Resetar dados de usuário (ADM)"
            ),
            inline=False
        )

        # 🤖 Informações
        embed.add_field(
            name="🤖 Informações",
            value=(
                "`/apresentacao` → Conhecer a Véu\n"
                "`/ajuda` → Ver todos os comandos"
            ),
            inline=False
        )

        embed.set_footer(
            text="Véu Entre Mundos • Comandos administrativos são restritos"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


    # =========================
    # /apresentacao
    # =========================
    @app_commands.command(
        name="apresentacao",
        description="Conheça a Véu, guardiã do Véu Entre Mundos"
    )
    async def apresentacao(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🕯️ VÉU — A GUARDIÃ DO VÉU 🕯️",
            description=(
                "Eu sou **Véu**.\n\n"
                "Entre mundos, fragmentos e ecos esquecidos,\n"
                "sou a voz que organiza o caos e observa o invisível.\n\n"
                "💎 Gerencio a economia de fragmentos.\n"
                "🎫 Administro tickets e suporte.\n"
                "📜 Registro decisões e eventos.\n"
                "🛒 Controlo a Loja e suas raridades.\n"
                "📊 Mantenho o ranking sob vigilância.\n\n"
                "Se precisar de ajuda, chame.\n"
                "Se tentar quebrar as regras… eu verei."
            ),
            color=config.COLOR_PRIMARY
        )

        embed.set_footer(
            text="Véu Entre Mundos • Nada passa despercebido"
        )

        await interaction.response.send_message(embed=embed)


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Ajuda(bot))