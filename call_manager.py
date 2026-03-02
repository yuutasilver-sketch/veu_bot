import time
import discord
from discord.ext import commands

from database import load_json, save_json, ensure_user
from config import USERS_DB, CALLS_DB


class CallManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("🔥 CallManager carregado com sucesso")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # ignora eventos inúteis (mute, deaf, etc)
        if before.channel == after.channel:
            return

        users = load_json(USERS_DB, {})
        calls = load_json(CALLS_DB, {})

        user_id = member.id
        user_key = str(member.id)
        agora = int(time.time())

        # garante usuário no users.json
        user = ensure_user(users, user_id)

        # ───── ENTROU EM CALL ─────
        if before.channel is None and after.channel is not None:
            calls[user_key] = {
                "start": agora
            }

            save_json(CALLS_DB, calls)
            save_json(USERS_DB, users)

            print(f"🎧 {member.name} entrou em call")

        # ───── TROCOU DE CALL ─────
        elif before.channel is not None and after.channel is not None:
            if user_key in calls:
                inicio = calls[user_key]["start"]
                tempo = agora - inicio

                user["tempo_call"] = user.get("tempo_call", 0) + tempo

                # reinicia contador
                calls[user_key]["start"] = agora

                save_json(USERS_DB, users)
                save_json(CALLS_DB, calls)

                print(f"🔁 {member.name} trocou de call (+{tempo}s)")

        # ───── SAIU DA CALL ─────
        elif before.channel is not None and after.channel is None:
            if user_key in calls:
                inicio = calls[user_key]["start"]
                tempo = agora - inicio

                user["tempo_call"] = user.get("tempo_call", 0) + tempo

                del calls[user_key]

                save_json(USERS_DB, users)
                save_json(CALLS_DB, calls)

                print(f"📴 {member.name} saiu da call (+{tempo}s)")


async def setup(bot):
    await bot.add_cog(CallManager(bot))
