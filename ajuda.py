# ajuda.py — COMANDOS DE AJUDA + LINK PARA O SITE

import discord
from discord import app_commands
from discord.ext import commands

import config
from database import get_guild_config, premium_message  # Corrigido: premium_message completo
from views import SiteButtonView

class Ajuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /ajuda
    @app_commands.command(name="ajuda", description="Mostra todos os comandos do Véu")
    async def ajuda(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg["bot_enabled"]:
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        embed = discord.Embed(
            title="🕯️ Guia do Guardião do Véu",
            description=(
                "Bem-vindo ao Véu Entre Mundos. Aqui estão os comandos para navegar nesta jornada eterna.\n\n"
                "**Comandos disponíveis:** (use / para slash commands)"
            ),
            color=0x4b0082
        )

        # Economia
        embed.add_field(
            name="💎 Economia",
            value=(
                "/saldo: Contemple seus fragmentos eternos\n"
                "/daily: Resgate oferenda diária\n"
                "/weekly: Resgate oferenda semanal\n"
                "/work: Trabalhe para ganhar fragmentos\n"
                "/roubar: Tente roubar fragmentos (cuidado!)"
            ),
            inline=False
        )

        # Social
        embed.add_field(
            name="♡ Social",
            value=(
                "/perfil: Veja seu perfil eterno\n"
                "/amigos: Gerencie laços de amizade\n"
                "/casar: Una almas no Véu\n"
                "/divorciar: Rompa laços eternos\n"
                "/reputar: Dê reputação a outro viajante"
            ),
            inline=False
        )

        # Tickets
        embed.add_field(
            name="📩 Tickets",
            value=(
                "/ticket: Invoque um portal de suporte\n"
                "/fechar_ticket: Feche o portal"
            ),
            inline=False
        )

        # Loja
        embed.add_field(
            name="🛒 Loja",
            value=(
                "/loja: Abra o bazar eterno\n"
                "/loja_cor: Tingir sua aura\n"
                "/presentes: Ofereça dons a outros"
            ),
            inline=False
        )

        # Missões e Ranking
        embed.add_field(
            name="🏆 Missões & Ranking",
            value=(
                "/missoes: Veja desafios do Véu\n"
                "/ranking: Contemple os mais poderosos\n"
                "/nivel: Veja sua ascensão"
            ),
            inline=False
        )

        # Outros
        embed.add_field(
            name="⚙️ Outros",
            value=(
                "/anon_confissao: Envie segredos anônimos\n"
                "/evento: Participe de drops eternos\n"
                "/ajuda: Este guia (recursivo!)"
            ),
            inline=False
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1428432707284762654/1477310985504034999/ideogram-v3.0_circular_gothic_arcane_logo_badge_for_discord_bot_Veu_elegant_dark_red_wine_cri-0-Photoroom.png")

        embed.set_footer(text="Feito com sangue e neon • Akisil")

        await interaction.response.send_message(embed=embed)
        await interaction.followup.send(
            "🌐 Acesse o painel completo, loja e dashboard no site oficial:",
            view=SiteButtonView()
        )

async def setup(bot):
    await bot.add_cog(Ajuda(bot))