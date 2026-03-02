# akay.py — AKAY (SÓ VOCÊ TEM ACESSO TOTAL)

import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import random
import config
from database import load_json, save_json, ensure_user

OWNER_ID = 551080982493528106  # Seu ID

class Akay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modo_ocupado = False
        self.status_loop.start()

    def cog_unload(self):
        self.status_loop.cancel()

    # STATUS AUTOMÁTICO
    @tasks.loop(minutes=30)
    async def status_loop(self):
        statuses = [
            discord.Game("entre mundos..."),
            discord.Activity(type=discord.ActivityType.watching, name="o Véu"),
            discord.Activity(type=discord.ActivityType.listening, name="sussurros"),
            discord.Game("com Akisil 🔮")
        ]
        await self.bot.change_presence(activity=random.choice(statuses))

    # BLOQUEIA TODOS OS COMANDOS PARA QUEM NÃO É VOCÊ
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.modo_ocupado and message.author.id != OWNER_ID:
            if bot.user.mentioned_in(message):
                embed = discord.Embed(
                    title="🌙 Akay está ocupado",
                    description="Ele caminha além das camadas do Véu.\nAguarde seu retorno.",
                    color=discord.Color.dark_purple()
                )
                await message.channel.send(embed=embed)
                try:
                    await message.author.send("🔮 Akay está ocupado no momento.")
                except:
                    pass
                return

        await self.bot.process_commands(message)

    # COMANDO SECRETO SÓ PARA VOCÊ
    @commands.command(hidden=True)
    @commands.is_owner()
    async def ocupado(self, ctx):
        self.modo_ocupado = not self.modo_ocupado
        status = "ativado" if self.modo_ocupado else "desativado"
        await ctx.send(f"Modo ocupado {status}.")

    # COMANDO SECRETO SÓ PARA VOCÊ
    @commands.command(hidden=True)
    @commands.is_owner()
    async def status(self, ctx, *, text):
        await self.bot.change_presence(activity=discord.Game(name=text))
        await ctx.send(f"Status alterado para: {text}")

async def setup(bot):
    await bot.add_cog(Akay(bot))