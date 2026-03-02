# guild_config.py — Configuração dinâmica por servidor

import json
import os
from config import GUILDS_DB, DEFAULT_GUILD_CONFIG
import discord
from database import load_json, save_json

def load_guilds():
    return load_json(GUILDS_DB, {})

def save_guilds(data):
    save_json(GUILDS_DB, data)

def get_guild_config(guild_id):
    data = load_guilds()
    gid = str(guild_id)

    if gid not in data:
        data[gid] = DEFAULT_GUILD_CONFIG.copy()
        save_guilds(data)

    return data[gid]

def update_guild_config(guild_id, key, value):
    data = load_guilds()
    gid = str(guild_id)

    if gid not in data:
        data[gid] = DEFAULT_GUILD_CONFIG.copy()

    data[gid][key] = value
    save_guilds(data)

def get_setting(guild_id, key, default=None):
    cfg = get_guild_config(guild_id)
    return cfg.get(key, default)

def is_bot_enabled(guild_id):
    return get_setting(guild_id, "bot_enabled", True)

def premium_message():
    embed = discord.Embed(
        title="🔒 Recurso Premium",
        description="Este recurso está disponível apenas para servidores premium.\n\nCompre premium no nosso site e libere tudo!",
        color=0x8B0000
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1428432707284762654/1477310985504034999/ideogram-v3.0_circular_gothic_arcane_logo_badge_for_discord_bot_Veu_elegant_dark_red_wine_cri-0-Photoroom.png")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Comprar Premium",
        url="https://veu-entre-mundos.netlify.app",
        style=discord.ButtonStyle.danger,
        emoji="🔥"
    ))

    return embed, view