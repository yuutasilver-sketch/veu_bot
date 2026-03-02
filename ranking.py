# ranking.py — SISTEMA DE RANKING (MULTI-SERVIDOR + DASHBOARD)

import discord
from discord import app_commands
from discord.ext import commands

import config
from database import load_json, get_guild_config, is_premium, premium_message

USERS_DB = config.USERS_DB
MISSOES_DB = config.MISSOES_DB


# =========================
# UTIL
# =========================

def sort_users(users: dict, key: str):
    return sorted(
        users.items(),
        key=lambda x: x[1].get(key, 0),
        reverse=True
    )


def sort_missoes(missoes: dict):
    ranking = []

    for uid, data in missoes.items():
        total = sum(1 for missao in data.values() if missao.get("completada", False))
        ranking.append((uid, total))

    return sorted(ranking, key=lambda x: x[1], reverse=True)


# =========================
# VIEW PARA PAGINAR RANKING
# =========================
class RankView(discord.ui.View):
    def __init__(self, bot, interaction, ordered, tipo):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction
        self.ordered = ordered
        self.tipo = tipo
        self.page = 0
        self.max_page = (len(ordered) - 1) // 10

        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.children[0].disabled = self.page == 0  # Anterior
        self.children[1].disabled = self.page == self.max_page  # Próxima

    @discord.ui.button(label="◀️ Véu Anterior", style=discord.ButtonStyle.secondary, emoji="🌑")
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.atualizar_botoes()
            embed = await self.build_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próximo Véu ▶️", style=discord.ButtonStyle.secondary, emoji="✨")
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
            self.atualizar_botoes()
            embed = await self.build_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def build_embed(self):
        start = self.page * 10
        end = start + 10
        slice_list = self.ordered[start:end]

        embed = discord.Embed(
            title=f"🌑 Ranking do Véu — {self.tipo.capitalize()}",
            description=(
                "Os fragmentos eternos revelam os mais fortes entre os mundos...\n"
                "Quem dominará o Véu hoje?"
            ),
            color=0x4b0082,  # Roxo escuro neon místico
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/.../seu-logo-veu.png")  # Coloque o link do seu logo do Véu aqui

        for idx, (uid, valor) in enumerate(slice_list, start + 1):
            user = self.bot.get_user(int(uid))
            nome = user.display_name if user else f"Alma Perdida (ID {uid})"

            medal = ""
            if idx == 1:
                medal = "👑 **Primeiro do Véu** "
            elif idx == 2:
                medal = "🥈 **Guardião do Véu** "
            elif idx == 3:
                medal = "🥉 **Eco do Véu** "

            embed.add_field(
                name=f"{medal}#{idx} • {nome}",
                value=f"**{valor:,}** {self.tipo.capitalize()}",
                inline=False
            )

        embed.set_footer(
            text="Véu Entre Mundos • Os fragmentos contam histórias... • Página {}/{}".format(self.page + 1, self.max_page + 1),
            icon_url="https://cdn.discordapp.com/emojis/1101234567890123456.png"  # Emoji temático (opcional)
        )

        return embed


# =========================
# COG RANKING
# =========================
class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="Contemple o ranking dos que mais brilham no Véu")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Experiência (XP)", value="xp"),
        app_commands.Choice(name="Reputação", value="reputacao"),
        app_commands.Choice(name="Tempo em Voz", value="tempo_call"),
        app_commands.Choice(name="Fragmentos", value="fragmentos"),
        app_commands.Choice(name="Missões Completadas", value="missoes")
    ])
    async def ranking(self, interaction: discord.Interaction, tipo: str = "xp"):

        await interaction.response.defer()

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("ranking_enabled", True):
            embed, view = premium_message()
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        if not is_premium(guild_id) and tipo == "missoes":
            embed, view = premium_message()
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        users = load_json(USERS_DB, {})
        missoes = load_json(MISSOES_DB, {})

        if tipo == "missoes":
            ordered = sort_missoes(missoes)[:50]
        else:
            ordered = sort_users(users, tipo)[:50]

        if not ordered:
            embed = discord.Embed(
                title="🌑 O Véu está silencioso...",
                description="Nenhum viajante deixou sua marca ainda.",
                color=0x2f004f
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        view = RankView(self.bot, interaction, ordered, tipo)
        embed = await view.build_embed()

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Ranking(bot))