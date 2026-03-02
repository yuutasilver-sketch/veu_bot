import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

from database import load_json, save_json, ensure_user
import config


# =========================
# CONFIGURAÇÃO DAS CORES
# =========================

CORES_DISPONIVEIS = {
    "Violeta do Véu": {"valor": 1500, "hex": 0x8e44ad},
    "Azul Abissal": {"valor": 1200, "hex": 0x1f3a93},
    "Rosa Arcano": {"valor": 1000, "hex": 0xff4da6},
    "Verde Éter": {"valor": 900, "hex": 0x2ecc71},
    "Dourado Celestial": {"valor": 2000, "hex": 0xf1c40f},
    "Vermelho Carmesim": {"valor": 1300, "hex": 0xc0392b},
    "Cinza Fantasma": {"valor": 600, "hex": 0x95a5a6},
    "Branco Astral": {"valor": 500, "hex": 0xecf0f1},
    "Preto Cósmico": {"valor": 1800, "hex": 0x2c3e50},
    "Lilás Nebuloso": {"valor": 1100, "hex": 0xc39bd3},
    "Ciano Espiritual": {"valor": 800, "hex": 0x1abc9c},
    "Laranja Eclipse": {"valor": 700, "hex": 0xe67e22},
    "Azul Gélido": {"valor": 400, "hex": 0x5dade2},
    "Magenta Sombrio": {"valor": 1400, "hex": 0x9b59b6},
    "Verde Profundo": {"valor": 100, "hex": 0x145a32},
}

VIP_DESCONTO = 0.20
VIP_PRECO = 1_000_000
CARGO_BASE_ID = 1462160787840700442


# =========================
# VIEW PERSISTENTE
# =========================

class LojaCorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        row = 0
        count = 0

        for nome_cor, dados in CORES_DISPONIVEIS.items():
            self.add_item(
                BotaoCor(
                    nome_cor,
                    dados["valor"],
                    dados["hex"],
                    row=row
                )
            )
            count += 1
            if count % 5 == 0:
                row += 1

        self.add_item(BotaoVIP(row=row + 1))


# =========================
# BOTÃO COR
# =========================

class BotaoCor(discord.ui.Button):
    def __init__(self, nome, valor, cor_hex, row):
        super().__init__(
            label=f"{nome} • {valor}",
            style=discord.ButtonStyle.secondary,
            emoji="🎨",
            row=row,
            custom_id=f"loja_cor_{nome.lower().replace(' ', '_')}"
        )

        self.nome = nome
        self.valor = valor
        self.cor_hex = cor_hex

    async def callback(self, interaction: discord.Interaction):

        if not interaction.guild:
            return

        users = load_json(config.USERS_DB, {})
        ensure_user(users, interaction.user.id)

        user_id = str(interaction.user.id)
        valor_final = self.valor

        vip_role = interaction.guild.get_role(config.VIP_ROLE_ID)
        is_vip = vip_role and vip_role in interaction.user.roles

        if is_vip:
            valor_final = int(self.valor * (1 - VIP_DESCONTO))

        if users[user_id]["fragmentos"] < valor_final:
            return await interaction.response.send_message(
                f"❌ Você precisa de {valor_final} {config.CURRENCY_NAME}.",
                ephemeral=True
            )

        # Remove cores antigas
        for role in interaction.user.roles:
            if role.name in CORES_DISPONIVEIS:
                try:
                    await interaction.user.remove_roles(role)
                except:
                    pass

        role = discord.utils.get(interaction.guild.roles, name=self.nome)

        # 🔥 CRIA E POSICIONA O CARGO CORRETAMENTE
        if role is None:
            try:
                role = await interaction.guild.create_role(
                    name=self.nome,
                    color=discord.Color(self.cor_hex),
                    reason="Compra de cor na Loja"
                )

                # Rebusca o cargo após criação
                role = interaction.guild.get_role(role.id)

                cargo_base = interaction.guild.get_role(CARGO_BASE_ID)

                if cargo_base:
                    await interaction.guild.edit_role_positions(
                        positions={
                            role: cargo_base.position + 1
                        }
                    )

            except discord.Forbidden:
                return await interaction.response.send_message(
                    "❌ Não tenho permissão para criar ou mover cargos.",
                    ephemeral=True
                )

        users[user_id]["fragmentos"] -= valor_final
        save_json(config.USERS_DB, users)

        await interaction.user.add_roles(role)

        embed = discord.Embed(
            title="✨ Cor Aplicada",
            description=f"🎨 **{self.nome}** ativada!\n💎 Custo: {valor_final} {config.CURRENCY_NAME}",
            color=self.cor_hex
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# BOTÃO VIP
# =========================

class BotaoVIP(discord.ui.Button):
    def __init__(self, row):
        super().__init__(
            label=f"Tornar-se VIP • {VIP_PRECO}",
            style=discord.ButtonStyle.primary,
            emoji="👑",
            row=row,
            custom_id="loja_vip"
        )

    async def callback(self, interaction: discord.Interaction):

        if not interaction.guild:
            return

        users = load_json(config.USERS_DB, {})
        ensure_user(users, interaction.user.id)

        user_id = str(interaction.user.id)

        if users[user_id]["fragmentos"] < VIP_PRECO:
            return await interaction.response.send_message(
                f"❌ Você precisa de {VIP_PRECO} {config.CURRENCY_NAME}.",
                ephemeral=True
            )

        vip_role = interaction.guild.get_role(config.VIP_ROLE_ID)

        users[user_id]["fragmentos"] -= VIP_PRECO

        expira_em = datetime.utcnow() + timedelta(days=config.VIP_DURATION_DAYS)
        users[user_id]["vip_until"] = expira_em.isoformat()

        save_json(config.USERS_DB, users)

        await interaction.user.add_roles(vip_role)

        embed = discord.Embed(
            title="👑 VIP Ativado",
            description=f"VIP ativo por {config.VIP_DURATION_DAYS} dias!",
            color=0xf1c40f
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# COG
# =========================

class LojaCor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(LojaCorView())

    @app_commands.command(
        name="loja_cor_fixa",
        description="Envia a Loja de Cores fixa no canal (Somente ADM)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_cor_fixa(self, interaction: discord.Interaction):

        descricao = "Escolha sua cor personalizada.\n\n"

        for nome, dados in CORES_DISPONIVEIS.items():
            descricao += f"🎨 **{nome}** — {dados['valor']} {config.CURRENCY_NAME}\n"

        descricao += "\n👑 VIP recebe 20% de desconto\n🎭 Apenas uma cor ativa por vez"

        embed = discord.Embed(
            title="🎨 LOJA DE CORES — VÉU ENTRE MUNDOS",
            description=descricao,
            color=config.COLOR_PRIMARY
        )

        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1463584126316580986/1476283442101752032/ChatGPT_Image_25_de_fev._de_2026_15_23_03.png"
        )

        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1463584126316580986/1476289481975005236/ChatGPT_Image_25_de_fev._de_2026_15_47_03.png"
        )

        embed.set_footer(text="Véu Entre Mundos • Personalize sua essência")

        await interaction.response.send_message("✅ Loja enviada.", ephemeral=True)

        await interaction.channel.send(
            embed=embed,
            view=LojaCorView()
        )


async def setup(bot):
    await bot.add_cog(LojaCor(bot))