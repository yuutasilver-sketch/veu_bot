# views.py — Views persistentes do bot

import discord
from discord.ui import View, Button

# Botão para o site (usado em ajuda, perfil, premium block, etc.)
class SiteButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            Button(
                label="🌐 Ir para o Site",
                url="https://veu-entre-mundos.netlify.app",
                style=discord.ButtonStyle.link,
                emoji="🕯️"
            )
        )

# View persistente da loja (exemplo funcional - adapte os botões conforme sua loja.py)
class LojaView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistente

    @discord.ui.button(label="Comprar Item", style=discord.ButtonStyle.success, custom_id="loja_item")
    async def comprar_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Loja de itens aberta! (adicione lógica da loja aqui)", ephemeral=True)

    @discord.ui.button(label="Comprar Fundo", style=discord.ButtonStyle.primary, custom_id="loja_fundo")
    async def comprar_fundo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Loja de fundos aberta! (adicione lógica da loja aqui)", ephemeral=True)

    @discord.ui.button(label="Comprar Cor", style=discord.ButtonStyle.secondary, custom_id="loja_cor")
    async def comprar_cor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Loja de cores aberta! (adicione lógica da loja aqui)", ephemeral=True)