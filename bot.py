import os
from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyromod
import pyrogram.utils

# Solution de contournement pour autoriser les ID de canaux standard
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention  = me.mention
        self.username = me.username
        self.uptime   = Config.BOT_UPTIME

        # --- CORRECTION POUR RENDER ---
        # Ceci démarre le serveur web pour que Render ne tue pas votre bot
        app = web.AppRunner(await web_server())
        await app.setup()
        
        # Utilisation explicite du port 10000 (ou du PORT de l'environnement Render)
        port = int(os.environ.get("PORT", 10000))
        await web.TCPSite(app, "0.0.0.0", port).start()
        print(f"✅ Serveur web démarré sur le port {port} 🌐")
        # ------------------------------

        print(f"✨ {me.first_name} a démarré !.....✨️")

        # Notification aux administrateurs
        for admin_id in Config.ADMIN:
            try:
                await self.send_message(admin_id, f"**{me.first_name} a démarré...**")
            except Exception:
                pass

        # Envoi du journal (log) au canal
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} a redémarré !!**\n\n"
                    f"📅 Date : `{date}`\n"
                    f"⏰ Heure : `{time}`\n"
                    f"🌐 Fuseau horaire : `Asia/Kolkata`\n\n"
                    f"🉐 Version : `v{__version__} (Layer {layer})`"
                )
            except Exception:
                print("⚠️ Veuillez nommer ce bot Administrateur dans votre canal de journalisation (Log Channel)")


if __name__ == "__main__":
    Bot().run()
