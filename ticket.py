import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

import config
from database import load_json, save_json, ensure_user

TICKETS_DB = config.TICKETS_DB
USERS_DB = config.USERS_DB

PARCEIRO_ROLE_ID = 1466167038744461374

# =========================
# LOG
# =========================
async def send_log(guild, title, description, color):
    channel = guild.get_channel(config.TICKET_LOG_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    await channel.send(embed=embed)

# =========================
# MODAL PARCERIA
# =========================
class ParceriaModal(discord.ui.Modal, title="🤝 Solicitação de Parceria"):
    servidor = discord.ui.TextInput(label="Nome do servidor")
    membros = discord.ui.TextInput(label="Quantidade de membros")
    convite = discord.ui.TextInput(label="Link do servidor")
    descricao = discord.ui.TextInput(
        label="Descrição / Proposta",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    def __init__(self, interaction):
        super().__init__()
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        await criar_ticket(
            self.interaction,
            "parceria",
            {
                "Servidor": self.servidor.value,
                "Membros": self.membros.value,
                "Convite": self.convite.value,
                "Proposta": self.descricao.value
            }
        )

# =========================
# VIEW CONTROLE
# =========================
class TicketControlView(discord.ui.View):
    def __init__(self, tipo):
        super().__init__(timeout=None)
        self.tipo = tipo

        if tipo != "vip":
            self.remove_item(self.vip)

        if tipo != "parceria":
            self.remove_item(self.aprovar)
            self.remove_item(self.recusar)

    def is_staff(self, interaction):
        return any(r.id in config.TICKET_STAFF_ROLE_IDS for r in interaction.user.roles)

    @discord.ui.button(label="📌 Assumir Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_assumir")
    async def assumir(self, interaction: discord.Interaction, _):
        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)

        tickets = load_json(TICKETS_DB, {})
        ticket = tickets[str(interaction.channel.id)]

        if ticket["assumido_por"]:
            return await interaction.response.send_message("⚠️ Já assumido.", ephemeral=True)

        ticket["assumido_por"] = interaction.user.id
        save_json(TICKETS_DB, tickets)

        await send_log(
            interaction.guild,
            "📌 Ticket assumido",
            f"Staff: {interaction.user.mention}\nCanal: {interaction.channel.mention}",
            config.COLOR_PRIMARY
        )

        await interaction.response.send_message("✅ Ticket assumido.", ephemeral=True)

    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_fechar")
    async def fechar(self, interaction: discord.Interaction, _):
        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)

        tickets = load_json(TICKETS_DB, {})
        tickets[str(interaction.channel.id)]["status"] = "closed"
        save_json(TICKETS_DB, tickets)

        await interaction.channel.delete()

    @discord.ui.button(label="💎 Ativar VIP", style=discord.ButtonStyle.success, custom_id="ticket_vip")
    async def vip(self, interaction: discord.Interaction, _):
        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)

        tickets = load_json(TICKETS_DB, {})
        ticket = tickets[str(interaction.channel.id)]
        user_id = ticket["user"]

        member = interaction.guild.get_member(user_id)
        role = interaction.guild.get_role(config.VIP_ROLE_ID)

        if member and role:
            await member.add_roles(role)

        users = load_json(USERS_DB, {})
        data = ensure_user(users, user_id)
        data["vip_until"] = (
            datetime.utcnow() + timedelta(days=config.VIP_DURATION_DAYS)
        ).isoformat()
        save_json(USERS_DB, users)

        await send_log(
            interaction.guild,
            "💎 VIP ativado",
            f"Usuário: {member.mention}\nStaff: {interaction.user.mention}",
            config.COLOR_SUCCESS
        )

        await interaction.response.send_message("💎 VIP ativado.", ephemeral=True)

    @discord.ui.button(label="✅ Aprovar Parceria", style=discord.ButtonStyle.success, custom_id="ticket_aprovar_parceria")
    async def aprovar(self, interaction: discord.Interaction, _):
        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)

        tickets = load_json(TICKETS_DB, {})
        ticket = tickets[str(interaction.channel.id)]
        member = interaction.guild.get_member(ticket["user"])

        if member:
            role = interaction.guild.get_role(PARCEIRO_ROLE_ID)
            if role:
                await member.add_roles(role)

        canal = interaction.guild.get_channel(config.PARCERIA_APROVADA_CHANNEL_ID)
        if canal:
            embed = discord.Embed(
                title="🤝 Nova Parceria Aprovada",
                color=config.COLOR_SUCCESS,
                timestamp=datetime.utcnow()
            )
            for k, v in ticket["dados"].items():
                embed.add_field(name=k, value=v, inline=False)
            await canal.send(embed=embed)

        if member:
            try:
                await member.send("✅ Sua proposta de parceria foi **APROVADA**!")
            except:
                pass

        ticket["status"] = "closed"
        save_json(TICKETS_DB, tickets)
        await interaction.channel.delete()

    @discord.ui.button(label="❌ Recusar Parceria", style=discord.ButtonStyle.danger, custom_id="ticket_recusar_parceria")
    async def recusar(self, interaction: discord.Interaction, _):
        if not self.is_staff(interaction):
            return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)

        tickets = load_json(TICKETS_DB, {})
        ticket = tickets[str(interaction.channel.id)]
        member = interaction.guild.get_member(ticket["user"])

        if member:
            try:
                await member.send("❌ Sua proposta de parceria foi **RECUSADA**.")
            except:
                pass

        ticket["status"] = "closed"
        save_json(TICKETS_DB, tickets)
        await interaction.channel.delete()

# =========================
# CRIAR TICKET
# =========================
async def criar_ticket(interaction, tipo, dados=None):
    guild = interaction.guild
    user = interaction.user
    tickets = load_json(TICKETS_DB, {})

    category = guild.get_channel(config.TICKET_CATEGORY_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True)
    }

    for rid in config.TICKET_STAFF_ROLE_IDS:
        role = guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True)

    channel = await guild.create_text_channel(
        f"{tipo}-{user.name}",
        category=category,
        overwrites=overwrites
    )

    tickets[str(channel.id)] = {
        "user": user.id,
        "tipo": tipo,
        "status": "open",
        "created": datetime.utcnow().isoformat(),
        "assumido_por": None,
        "dados": dados
    }

    save_json(TICKETS_DB, tickets)

    embed = discord.Embed(
        title=f"🎫 Ticket de {tipo.upper()}",
        description="Explique sua solicitação com detalhes.",
        color=config.COLOR_PRIMARY
    )

    if dados:
        for k, v in dados.items():
            embed.add_field(name=k, value=v, inline=False)

    await channel.send(
        content=user.mention,
        embed=embed,
        view=TicketControlView(tipo)
    )

    await interaction.response.send_message(
        f"✅ Ticket criado: {channel.mention}",
        ephemeral=True
    )

# =========================
# PAINEL FIXO
# =========================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecione uma opção",
            custom_id="ticket_select",
            options=[
                discord.SelectOption(label="Denúncia", value="denuncia", emoji="🚨"),
                discord.SelectOption(label="Sugestão", value="sugestao", emoji="💡"),
                discord.SelectOption(label="Parceria", value="parceria", emoji="🤝"),
                discord.SelectOption(label="VIP", value="vip", emoji="💎"),
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "parceria":
            await interaction.response.send_modal(ParceriaModal(interaction))
        else:
            await criar_ticket(interaction, self.values[0])

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# =========================
# COG
# =========================
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketPanelView())

    @app_commands.command(name="ticket_painel", description="Abre o painel de tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_painel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🕯️ CENTRAL DE AJUDA — VÉU ENTRE MUNDOS 🕯️",
            description=config.TICKET_PANEL_TEXT,
            color=config.COLOR_PRIMARY
        )

        if config.TICKET_IMAGE_URL:
            embed.set_image(url=config.TICKET_IMAGE_URL)

        await interaction.response.send_message(embed=embed, view=TicketPanelView())

async def setup(bot):
    await bot.add_cog(Ticket(bot))
