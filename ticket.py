# ticket.py — SISTEMA DE TICKETS (MULTI-SERVIDOR + DASHBOARD INTEGRADA)

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

import config
from database import load_json, save_json, ensure_user, get_guild_config, is_premium, premium_message, now_iso, iso_to_dt

TICKETS_DB = config.TICKETS_DB
USERS_DB = config.USERS_DB


# =========================
# VIEW PARA BOTÕES DE TICKETS (DINÂMICA DA DASHBOARD)
# =========================
class TicketView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        cfg = get_guild_config(guild_id)

        # Botões dinâmicos vindos da dashboard
        buttons = cfg.get("tickets_buttons", [])

        for btn in buttons:
            button = discord.ui.Button(
                label=btn.get("label", "Abrir Ticket"),
                style=discord.ButtonStyle.primary,
                emoji=btn.get("emoji"),
                custom_id=f"ticket_{btn.get('categoria', 'geral')}"
            )
            button.callback = self.abrir_ticket
            self.add_item(button)


    async def abrir_ticket(self, interaction: discord.Interaction):
        guild_id = self.guild_id
        cfg = get_guild_config(guild_id)

        if not cfg.get("tickets_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        categoria = interaction.data["custom_id"].split("_")[1]  # ex: "geral"

        # Verifica limite de tickets por usuário
        tickets = load_json(TICKETS_DB, {})
        user_tickets = [t for t in tickets.values() if t["user_id"] == interaction.user.id and t["status"] == "aberto"]
        max_tickets = cfg.get("tickets_max_por_user", 3)
        if len(user_tickets) >= max_tickets:
            return await interaction.response.send_message(
                f"🌑 O Véu limita a {max_tickets} portais abertos por alma... Feche um antes de invocar outro.",
                ephemeral=True
            )

        # Cria canal privado
        guild = interaction.guild
        category_id = cfg.get("tickets_category")
        category = guild.get_channel(category_id) if category_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)
        }

        # Adiciona staff roles
        staff_roles = cfg.get("tickets_staff_roles", [])
        for role_id in staff_roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)

        canal_nome = f"ticket-{interaction.user.name}-{categoria}".lower()
        channel = await guild.create_text_channel(
            name=canal_nome,
            category=category,
            overwrites=overwrites,
            reason="Ticket criado pelo Véu"
        )

        # Salva no DB
        ticket_id = str(channel.id)
        tickets[ticket_id] = {
            "user_id": interaction.user.id,
            "categoria": categoria,
            "criado_em": now_iso(),
            "criador_nome": interaction.user.display_name,
            "canal_nome": canal_nome,
            "status": "aberto"
        }
        save_json(TICKETS_DB, tickets)

        # Embed imersiva no ticket
        embed_ticket = discord.Embed(
            title="🌑 Portal do Véu Aberto",
            description=(
                f"**Viajante {interaction.user.mention}**, bem-vindo ao seu portal privado entre os mundos.\n\n"
                "Descreva sua jornada, dúvida ou oferenda, e os Guardiões do Véu (staff) responderão.\n"
                f"**Categoria invocada**: {categoria.capitalize()}\n"
                "Feche este portal quando sua alma estiver em paz."
            ),
            color=0x4b0082,
            timestamp=datetime.utcnow()
        )
        embed_ticket.set_footer(text="Véu Entre Mundos • Seu segredo está selado aqui ♾️")

        # View para fechar
        class FecharView(discord.ui.View):
            @discord.ui.button(label="Fechar Portal", style=discord.ButtonStyle.danger, emoji="🔒")
            async def fechar(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != interaction.user.id and not inter.user.guild_permissions.administrator:
                    return await inter.response.send_message("❌ Apenas o viajante ou Guardiões podem selar este portal.", ephemeral=True)

                # Calcula tempo aberto
                criado = iso_to_dt(tickets[ticket_id]["criado_em"])
                tempo_aberto = datetime.utcnow() - criado if criado else timedelta(seconds=0)
                horas = tempo_aberto.seconds // 3600
                minutos = (tempo_aberto.seconds % 3600) // 60

                # Log detalhado de fechamento
                await self.enviar_log_fechamento(inter, tickets[ticket_id], tempo_aberto)

                tickets[ticket_id]["status"] = "fechado"
                tickets[ticket_id]["fechado_em"] = now_iso()
                tickets[ticket_id]["fechado_por"] = inter.user.id
                save_json(TICKETS_DB, tickets)

                await channel.delete(reason="Ticket fechado pelo Véu")

        await channel.send(embed=embed_ticket, view=FecharView())

        # Log detalhado de criação
        await self.enviar_log_criacao(interaction, tickets[ticket_id], channel)

        await interaction.response.send_message(
            f"✨ Seu portal foi invocado com sucesso: {channel.mention}.\n"
            "O Véu o protege enquanto sua jornada se desenrola.",
            ephemeral=True
        )


    async def enviar_log_criacao(self, interaction: discord.Interaction, ticket_data: dict, channel: discord.TextChannel):
        cfg = get_guild_config(interaction.guild.id)
        log_channel_id = cfg.get("tickets_logs")
        if not log_channel_id:
            return

        log_channel = interaction.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed_log = discord.Embed(
            title="🌑 Novo Portal Invocado no Véu",
            color=0x9c27b0,  # Roxo vibrante
            timestamp=datetime.utcnow()
        )
        embed_log.add_field(name="Viajante", value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
        embed_log.add_field(name="Categoria", value=ticket_data["categoria"].capitalize(), inline=True)
        embed_log.add_field(name="Canal Criado", value=channel.mention, inline=True)
        embed_log.add_field(name="Data de Invocação", value=discord.utils.format_dt(datetime.utcnow(), "F t"), inline=False)
        embed_log.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed_log.set_footer(text="Véu Entre Mundos • Logs Eternos ♾️")

        await log_channel.send(embed=embed_log)


    async def enviar_log_fechamento(self, interaction: discord.Interaction, ticket_data: dict, tempo_aberto: timedelta):
        cfg = get_guild_config(interaction.guild.id)
        log_channel_id = cfg.get("tickets_logs")
        if not log_channel_id:
            return

        log_channel = interaction.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        fechador = interaction.user
        criador = interaction.guild.get_member(ticket_data["user_id"])
        criador_nome = criador.display_name if criador else f"ID {ticket_data['user_id']}"

        horas = tempo_aberto.seconds // 3600
        minutos = (tempo_aberto.seconds % 3600) // 60

        embed_log = discord.Embed(
            title="🖤 Portal Selado no Véu",
            color=0x455a64,  # Cinza escuro melancólico
            timestamp=datetime.utcnow()
        )
        embed_log.add_field(name="Viajante", value=f"{criador_nome} ({ticket_data['user_id']})", inline=True)
        embed_log.add_field(name="Fechado por", value=f"{fechador.mention} ({fechador.id})", inline=True)
        embed_log.add_field(name="Categoria", value=ticket_data["categoria"].capitalize(), inline=True)
        embed_log.add_field(name="Tempo Aberto", value=f"{horas}h {minutos}min", inline=True)
        embed_log.add_field(name="Canal", value=f"#{ticket_data['canal_nome']}", inline=False)
        embed_log.set_footer(text="Véu Entre Mundos • O laço foi desfeito ♾️")

        await log_channel.send(embed=embed_log)


# =========================
# COG TICKET
# =========================
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel_tickets", description="Invoca o painel de tickets no canal (ADM apenas)")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_tickets(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id
        cfg = get_guild_config(guild_id)

        if not cfg.get("tickets_enabled", True):
            embed, view = premium_message()
            return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        embed = discord.Embed(
            title="🌑 Portal de Invocações do Véu",
            description=(
                "Toque em um botão abaixo para abrir um portal privado entre os mundos.\n"
                "Os Guardiões do Véu (staff) responderão ao seu chamado."
            ),
            color=config.COLOR_PRIMARY,
            timestamp=datetime.utcnow()
        )

        image_url = cfg.get("tickets_panel_image")
        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(text="Véu Entre Mundos • Suporte Eterno ♾️")

        view = TicketView(guild_id)

        channel_id = cfg.get("tickets_panel_canal")
        channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("✅ O painel do Véu foi invocado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ticket(bot))