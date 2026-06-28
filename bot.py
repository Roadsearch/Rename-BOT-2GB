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

# Workaround to allow standard channel IDs
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

        # Combined Webhook & Render Ping Server Logic
        if Config.WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()
            # Dynamically grab the port assigned by your cloud provider (Render/Koyeb)
            port = int(os.environ.get("PORT", 8080))
            await web.TCPSite(app, "0.0.0.0", port).start()
            print(f"Web server started on port {port} 🌐")

        print(f"{me.first_name} Is Started.....✨️")

        # Notify Admins
        for admin_id in Config.ADMIN:
            try:
                await self.send_message(admin_id, f"**{me.first_name} Is Started...**")
            except Exception:
                pass

        # Send Log to Channel
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} Is Restarted !!**\n\n"
                    f"📅 Date : `{date}`\n"
                    f"⏰ Time : `{time}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`\n\n"
                    f"🉐 Version : `v{__version__} (Layer {layer})`"
                )
            except Exception:
                print("⚠️ Please Make This Bot Admin In Your Log Channel")


if __name__ == "__main__":
    Bot().run()
