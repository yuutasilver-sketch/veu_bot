import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta

from database import load_json, save_json, ensure_user
import config


# =========================================================
# VIEW DO EVENTO RELÂMPAGO (SEU SISTEMA ORIGINAL)
# =========================================================

class EventoRelampago(discord.ui.View):
    def __init__(self, bot, tipo, valor, canal_log):
        super().__init__(timeout=300)
        self.bot = bot
        self.tipo = tipo
        self.valor = valor
        self.claimed = False
        self.canal_log = canal_log

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="✨ Interagir com o Evento da Véu", style=discord.ButtonStyle.success)
    async def coletar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.claimed:
            await interaction.response.send_message(
                "⚠️ Alguém já interagiu com o evento!",
                ephemeral=True
            )
            return

        self.claimed = True
        button.disabled = True
        await interaction.message.edit(view=self)

        users = load_json(config.USERS_DB, {})
        missoes = load_json(config.MISSOES_FILE, {})

        ensure_user(users, interaction.user.id)

        user_id = str(interaction.user.id)
        users[user_id].setdefault("eventos_ganhos", 0)
        users[user_id].setdefault("eventos_raros", 0)

        resultado_msg = ""
        log_msg = ""

        if self.tipo == "normal":
            users[user_id]["fragmentos"] += self.valor
            users[user_id]["eventos_ganhos"] += 1
            resultado_msg = f"🌟 Evento Normal!\nVocê recebeu **{self.valor} {config.CURRENCY_NAME}!**"
            log_msg = f"[NORMAL] {interaction.user} ganhou {self.valor}"

        elif self.tipo == "raro":
            users[user_id]["fragmentos"] += self.valor
            users[user_id]["eventos_ganhos"] += 1
            users[user_id]["eventos_raros"] += 1
            resultado_msg = f"🌌 EVENTO RARO DA VÉU!\nVocê ganhou **{self.valor} {config.CURRENCY_NAME}!**"
            log_msg = f"[RARO] {interaction.user} ganhou {self.valor}"

        elif self.tipo == "falso":
            resultado_msg = "🎭 Evento Falso...\nEra apenas uma distorção do Véu."
            log_msg = f"[FALSO] {interaction.user}"

        elif self.tipo == "amaldiçoado":
            perda = min(self.valor, users[user_id]["fragmentos"])
            users[user_id]["fragmentos"] -= perda
            resultado_msg = f"💀 EVENTO AMALDIÇOADO!\nVocê perdeu **{perda} {config.CURRENCY_NAME}!**"
            log_msg = f"[AMALDIÇOADO] {interaction.user} perdeu {perda}"

        save_json(config.USERS_DB, users)
        save_json(config.MISSOES_FILE, missoes)

        await interaction.response.send_message(resultado_msg)

        if self.canal_log:
            await self.canal_log.send(
                f"📊 LOG EVENTOS DA VÉU • {datetime.now().strftime('%H:%M:%S')}\n{log_msg}"
            )

        self.stop()


# =========================================================
# VIEW DO DROP AUTOMÁTICO (NOVO)
# =========================================================

class DropView(discord.ui.View):
    def __init__(self, valor):
        super().__init__(timeout=60)
        self.valor = valor
        self.claimed = False

    @discord.ui.button(label="💎 Coletar Fragmentos", style=discord.ButtonStyle.primary)
    async def coletar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.claimed:
            await interaction.response.send_message(
                "⚠️ Este drop já foi coletado!",
                ephemeral=True
            )
            return

        self.claimed = True
        button.disabled = True
        await interaction.message.edit(view=self)

        users = load_json(config.USERS_DB, {})
        ensure_user(users, interaction.user.id)

        user_id = str(interaction.user.id)
        users[user_id]["fragmentos"] += self.valor

        save_json(config.USERS_DB, users)

        await interaction.response.send_message(
            f"💎 {interaction.user.mention} coletou **{self.valor} {config.CURRENCY_NAME}!**"
        )

        self.stop()


# =========================================================
# COG PRINCIPAL (EVENTOS + DROPS)
# =========================================================

class Evento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.proximo_evento = None
        self.ordem_eventos = ["amaldiçoado", "raro", "falso", "normal"]
        self.indice_evento = 0
        self.evento_task = bot.loop.create_task(self.loop_eventos())

    # =====================================================
    # COMANDO: PRÓXIMO EVENTO
    # =====================================================

    @app_commands.command(name="proximo_evento", description="Mostra quando será o próximo Evento da Véu")
    async def proximo_evento_cmd(self, interaction: discord.Interaction):

        if not self.proximo_evento:
            await interaction.response.send_message(
                "Nenhum evento agendado ainda.",
                ephemeral=True
            )
            return

        restante = self.proximo_evento - datetime.utcnow()
        segundos = int(restante.total_seconds())

        if segundos <= 0:
            await interaction.response.send_message("⚡ O evento está começando!", ephemeral=True)
            return

        horas = segundos // 3600
        minutos = (segundos % 3600) // 60

        await interaction.response.send_message(
            f"⏳ Próximo Evento da Véu em aproximadamente **{horas}h {minutos}m**"
        )

    # =====================================================
    # LOOP DOS EVENTOS DIÁRIOS (SEU SISTEMA)
    # =====================================================

    async def loop_eventos(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            espera = 86400
            self.proximo_evento = datetime.utcnow() + timedelta(seconds=espera)
            await asyncio.sleep(espera)

            canal = self.bot.get_channel(config.EVENTO_CANAL_ID)
            canal_log = self.bot.get_channel(config.EVENTO_LOG_CANAL_ID)

            if not canal:
                continue

            role = canal.guild.get_role(config.EVENTO_PING_ROLE_ID)
            tipo = self.ordem_eventos[self.indice_evento]

            if tipo == "normal":
                valor = 1500
                cor = 0x2ecc71
                titulo_extra = "🌟 Evento Normal"

            elif tipo == "raro":
                valor = 4000
                cor = 0x9b59b6
                titulo_extra = "🌌 Evento Raro"

            elif tipo == "falso":
                valor = 0
                cor = 0xf1c40f
                titulo_extra = "🎭 Evento Falso"

            elif tipo == "amaldiçoado":
                valor = 800
                cor = 0xe74c3c
                titulo_extra = "💀 Evento Amaldiçoado"

            self.indice_evento = (self.indice_evento + 1) % len(self.ordem_eventos)

            embed = discord.Embed(
                title="⚡ EVENTOS DA VÉU ⚡",
                description=(
                    f"{titulo_extra}\n\n"
                    "O Véu se distorceu novamente...\n"
                    "Clique primeiro e aceite seu destino.\n\n"
                    "⏳ Você tem 5 minutos."
                ),
                color=cor
            )

            view = EventoRelampago(self.bot, tipo, valor, canal_log)

            message = await canal.send(
                content=f"{role.mention} ⚡ Um Evento da Véu começou!" if role else None,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=True)
            )

            view.message = message

    # =====================================================
    # DROPS AUTOMÁTICOS POR MENSAGEM (NOVO)
    # =====================================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot or not message.guild:
            return

        # Chance de spawn (1 em X mensagens)
        chance = getattr(config, "DROP_CHANCE", 80)

        if random.randint(1, chance) != 1:
            return

        # Valor do drop
        valor = random.randint(
            getattr(config, "DROP_MIN", 50),
            getattr(config, "DROP_MAX", 150)
        )

        embed = discord.Embed(
            title="✨ Fragmento do Véu Detectado!",
            description=(
                "Uma energia escapou entre os mundos...\n"
                "Clique primeiro para capturar!"
            ),
            color=0x5865F2
        )

        view = DropView(valor)

        await message.channel.send(embed=embed, view=view)


# =========================================================
# SETUP
# =========================================================

async def setup(bot):
    await bot.add_cog(Evento(bot))