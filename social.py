# social.py — SISTEMA SOCIAL (MULTI-SERVIDOR + DASHBOARD INTEGRADA)

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

import config
from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message, now_iso, iso_to_dt

USERS_DB = config.USERS_DB

MARRIAGE_COST = 500
DIVORCE_COST = 300


# =========================
# GARANTIR CAMPOS SOCIAIS (GLOBAL)
# =========================
def ensure_social(data: dict):
    data.setdefault("friends", [])
    data.setdefault("married_to", None)
    data.setdefault("status_social", "Disponível")
    data.setdefault("humor", "Neutro")
    data.setdefault("reputacao", 0)
    data.setdefault("last_marriage", None)
    data.setdefault("cooldowns", {})


# =========================
# COG SOCIAL
# =========================
class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================
    # COMANDOS DE CASAMENTO
    # ==============================

    @app_commands.command(name="casar", description="Pedir alguém em casamento (custa 500 fragmentos)")
    async def casar(self, interaction: discord.Interaction, parceiro: discord.Member):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("social_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        if parceiro.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode casar consigo mesmo, alma gêmea solitária...", ephemeral=True)

        if parceiro.bot:
            return await interaction.response.send_message("❌ Nem os bots merecem tanto amor assim... Ainda.", ephemeral=True)

        users = load_json(USERS_DB, {})
        proposer = ensure_user(users, interaction.user.id)
        target = ensure_user(users, parceiro.id)
        ensure_social(proposer)
        ensure_social(target)

        # Verificações
        if proposer["married_to"]:
            return await interaction.response.send_message("❌ Seu coração já tem dono(a). Divorcie-se primeiro.", ephemeral=True)

        if target["married_to"]:
            parceiro_atual = self.bot.get_user(target["married_to"])
            nome = parceiro_atual.display_name if parceiro_atual else f"alguém misterioso (ID {target['married_to']})"
            return await interaction.response.send_message(f"❌ {parceiro.mention} já jurou amor eterno a {nome}.", ephemeral=True)

        if proposer["fragmentos"] < MARRIAGE_COST:
            return await interaction.response.send_message(
                f"💔 O Véu exige uma oferenda de **{MARRIAGE_COST} fragmentos** para selar um vínculo eterno...\n"
                f"Você tem apenas {proposer['fragmentos']}. Volte quando estiver pronto(a).",
                ephemeral=True
            )

        # Cooldown anti-spam (1 hora entre propostas)
        last_proposal = iso_to_dt(proposer["cooldowns"].get("marriage_proposal"))
        if last_proposal and (datetime.utcnow() - last_proposal) < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.utcnow() - last_proposal)
            mins = remaining.seconds // 60
            secs = remaining.seconds % 60
            return await interaction.response.send_message(
                f"🌙 O Véu pede paciência... Aguarde {mins}min {secs}s antes de propor novamente.",
                ephemeral=True
            )

        class CasamentoView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=600)  # 10 minutos para responder

            @discord.ui.button(label="Aceitar 💍", style=discord.ButtonStyle.green, emoji="💞")
            async def aceitar(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != parceiro.id:
                    await inter.response.send_message("❌ Apenas o(a) amado(a) pode selar esse destino.", ephemeral=True)
                    return

                # Realiza o casamento
                proposer["married_to"] = parceiro.id
                target["married_to"] = interaction.user.id
                proposer["last_marriage"] = now_iso()
                target["last_marriage"] = now_iso()
                proposer["fragmentos"] -= MARRIAGE_COST

                save_json(USERS_DB, users)

                embed = discord.Embed(
                    title="✨ União Eterna Selada no Véu ✧",
                    description=f"**{interaction.user.mention}** e **{parceiro.mention}**\n"
                                f"juraram amor perante os mundos entrelaçados!\n\n"
                                f"💍 Oferta aceita: {MARRIAGE_COST} fragmentos foram entregues ao Véu.",
                    color=0xff69b4,  # Rosa quente temático
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url="https://i.imgur.com/0wXjKzL.png")  # Imagem de alianças ou arte temática (substitua se quiser)
                embed.set_footer(text="Que o Véu proteja esse laço para sempre ♡")

                await inter.channel.send(embed=embed)
                await inter.response.defer()
                self.stop()

            @discord.ui.button(label="Recusar 💔", style=discord.ButtonStyle.red, emoji="🖤")
            async def recusar(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != parceiro.id:
                    await inter.response.send_message("❌ Apenas o(a) amado(a) pode recusar esse destino.", ephemeral=True)
                    return

                await inter.response.send_message(
                    f"🌑 {parceiro.mention} recusou o pedido de {interaction.user.mention}...\n"
                    "O Véu chora uma lágrima silenciosa.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
                self.stop()

        view = CasamentoView()

        embed_proposta = discord.Embed(
            title="💌 Pedido de Casamento do Véu",
            description=f"**{interaction.user.mention}** oferece seu coração a **{parceiro.mention}**!\n\n"
                        f"Valor simbólico: {MARRIAGE_COST} fragmentos (pago pelo proponente se aceito)\n"
                        "O Véu aguarda sua resposta por 10 minutos...",
            color=0x9c27b0,
            timestamp=datetime.utcnow()
        )
        embed_proposta.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message(embed=embed_proposta, view=view)

        # Registra cooldown
        proposer["cooldowns"]["marriage_proposal"] = now_iso()
        save_json(USERS_DB, users)

    @app_commands.command(name="divorciar", description="Dissolver o vínculo eterno (custa 300 fragmentos)")
    async def divorciar(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("social_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        users = load_json(USERS_DB, {})
        user = ensure_user(users, interaction.user.id)
        ensure_social(user)

        if not user["married_to"]:
            return await interaction.response.send_message("❌ Seu coração está livre... não há laço para romper.", ephemeral=True)

        parceiro_id = user["married_to"]
        parceiro_data = ensure_user(users, parceiro_id)
        ensure_social(parceiro_data)

        if user["fragmentos"] < DIVORCE_COST:
            return await interaction.response.send_message(
                f"🌑 O Véu exige **{DIVORCE_COST} fragmentos** como tributo para desfazer um laço eterno...\n"
                f"Você possui apenas {user['fragmentos']}. Volte quando estiver preparado(a).",
                ephemeral=True
            )

        parceiro = self.bot.get_user(parceiro_id)
        parceiro_nome = parceiro.display_name if parceiro else f"alguém distante (ID {parceiro_id})"

        class DivorcioView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

            @discord.ui.button(label="Confirmar Separação", style=discord.ButtonStyle.danger, emoji="💔")
            async def confirmar(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != interaction.user.id:
                    return

                user["married_to"] = None
                parceiro_data["married_to"] = None
                user["fragmentos"] -= DIVORCE_COST

                save_json(USERS_DB, users)

                embed = discord.Embed(
                    title="🖤 Laço Desfeito pelo Véu",
                    description=f"{interaction.user.mention} e {parceiro_nome} seguirão caminhos separados...\n"
                                f"O Véu cobrou {DIVORCE_COST} fragmentos como preço da liberdade.",
                    color=0x455a64,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Que ambos encontrem paz nos mundos entrelaçados")

                await inter.response.send_message(embed=embed)
                self.stop()

            @discord.ui.button(label="Manter o Laço", style=discord.ButtonStyle.secondary, emoji="💞")
            async def cancelar(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != interaction.user.id:
                    return
                await inter.response.send_message("O laço permanece intacto... por enquanto.", ephemeral=True)
                self.stop()

        view = DivorcioView()

        await interaction.response.send_message(
            f"⚠️ **{interaction.user.mention}**, você deseja realmente romper o vínculo com {parceiro_nome}?\n"
            f"Essa ação custará **{DIVORCE_COST} fragmentos** e é irreversível.",
            view=view,
            ephemeral=True
        )

    # /perfil_social (com data do casamento formatada)
    @app_commands.command(name="perfil_social", description="Ver o perfil social de alguém")
    async def perfil_social(self, interaction: discord.Interaction, membro: discord.Member = None):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("social_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        if membro is None:
            membro = interaction.user

        users = load_json(USERS_DB, {})
        user = ensure_user(users, membro.id)
        ensure_social(user)

        embed = discord.Embed(
            title=f"✧ Perfil Social — {membro.display_name} ✧",
            color=config.COLOR_PRIMARY,
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(url=membro.avatar.url if membro.avatar else membro.default_avatar.url)

        embed.add_field(name="Reputação", value=f"✦ {user['reputacao']} pontos", inline=True)
        embed.add_field(name="Estado Atual", value=user['status_social'], inline=True)
        embed.add_field(name="Humor", value=user['humor'], inline=True)

        if user["married_to"]:
            parceiro = self.bot.get_user(user["married_to"])
            nome = parceiro.display_name if parceiro else f"Alma misteriosa (ID {user['married_to']})"
            data_casamento = iso_to_dt(user["last_marriage"])
            data_str = data_casamento.strftime("%d de %B de %Y às %H:%M") if data_casamento else "em um tempo esquecido"
            embed.add_field(
                name="Vínculo Eterno",
                value=f"**Casado(a) com {nome}**\nDesde: {data_str}",
                inline=False
            )
        else:
            embed.add_field(name="Coração Livre", value="Solteiro(a) e aberto(a) aos ventos do Véu", inline=False)

        friends_list = [f"<@{fid}>" for fid in user["friends"][:8]]
        friends_str = ", ".join(friends_list) + (f" +{len(user['friends'])-8} outros" if len(user["friends"]) > 8 else "")
        embed.add_field(name="Laços de Amizade", value=friends_str or "Ainda sem companheiros de jornada", inline=False)

        embed.set_footer(text="Véu Entre Mundos • Social • ♡")

        await interaction.response.send_message(embed=embed)


    # ... (outros comandos como reputar, addfriend, removefriend, sethumor, setstatus permanecem iguais à versão anterior)


async def setup(bot):
    await bot.add_cog(Social(bot))