import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import time

import config

ARQUIVO_ECONOMIA = "database/economia.json"
ARQUIVO_WEEKLY = "database/weekly.json"

RECOMPENSA_WEEKLY = 1500  # ajuste se quiser


class Weekly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # cria arquivos se não existirem
        if not os.path.exists(ARQUIVO_WEEKLY):
            with open(ARQUIVO_WEEKLY, "w") as f:
                json.dump({}, f)


    def carregar_economia(self):
        if not os.path.exists(ARQUIVO_ECONOMIA):
            with open(ARQUIVO_ECONOMIA, "w") as f:
                json.dump({}, f)

        with open(ARQUIVO_ECONOMIA, "r") as f:
            return json.load(f)


    def salvar_economia(self, data):
        with open(ARQUIVO_ECONOMIA, "w") as f:
            json.dump(data, f, indent=4)


    def carregar_weekly(self):
        with open(ARQUIVO_WEEKLY, "r") as f:
            return json.load(f)


    def salvar_weekly(self, data):
        with open(ARQUIVO_WEEKLY, "w") as f:
            json.dump(data, f, indent=4)


    # =========================
    # /weekly
    # =========================
    @app_commands.command(
        name="weekly",
        description="Resgate sua recompensa semanal de fragmentos"
    )
    async def weekly(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)
        agora = int(time.time())

        weekly_data = self.carregar_weekly()
        economia = self.carregar_economia()

        if user_id not in economia:
            economia[user_id] = {
                "fragmentos": 0,
                "nivel": 0,
                "xp": 0
            }

        ultimo_resgate = weekly_data.get(user_id, 0)

        tempo_restante = 604800 - (agora - ultimo_resgate)  # 7 dias em segundos

        if tempo_restante > 0:
            dias = tempo_restante // 86400
            horas = (tempo_restante % 86400) // 3600
            minutos = (tempo_restante % 3600) // 60

            embed = discord.Embed(
                title="⏳ Weekly já resgatado",
                description=(
                    f"Você já coletou sua recompensa semanal.\n\n"
                    f"🕒 Disponível novamente em:\n"
                    f"**{dias}d {horas}h {minutos}m**"
                ),
                color=discord.Color.red()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # adicionar recompensa
        economia[user_id]["fragmentos"] += RECOMPENSA_WEEKLY
        weekly_data[user_id] = agora

        self.salvar_economia(economia)
        self.salvar_weekly(weekly_data)

        embed = discord.Embed(
            title="🎁 Recompensa Semanal Resgatada",
            description=(
                f"Você recebeu **{RECOMPENSA_WEEKLY:,} fragmentos** 💎\n\n"
                "O Véu recompensa aqueles que permanecem ativos..."
            ),
            color=config.COLOR_PRIMARY
        )

        embed.set_footer(text="Volte em 7 dias para resgatar novamente")

        await interaction.response.send_message(embed=embed)


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Weekly(bot))