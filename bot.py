from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import os
import pyromod
import pyrogram.utils

pyrogram.utils.MIN_CHANNEL_ID = -1002909111512


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
        self.mention = me.mention
        self.username = me.username  
        self.uptime = Config.BOT_UPTIME     
        if Config.WEBHOOK:
            port = int(os.environ.get("PORT", 8080))
            app = web.AppRunner(await web_server())
            await app.setup()       
            await web.TCPSite(app, "0.0.0.0", port).start()     
        print(f"{me.first_name} Est Démarré.....✨️")
        for id in Config.ADMIN:
            try: await self.send_message(id, f"**{me.first_name}  Est Démarré...**")                                
            except: pass
        
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Africa/Dakar"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(Config.LOG_CHANNEL, f"**{me.mention} A Redémarré !!**\n\n📅 Date : `{date}`\n⏰ Heure : `{time}`\n🌐 Fuseau horaire : `Africa/Dakar`\n\n🉐 Version : `v{__version__} (Layer {layer})`</b>")                                
            except:
                print("Merci d'ajouter ce bot comme admin dans votre canal de logs")

Bot().run()






# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
