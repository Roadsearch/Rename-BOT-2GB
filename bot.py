import logging
import asyncio
from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyromod
import pyrogram.utils

pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# FileHandler pour /getlog — défini ici directement sans import circulaire
_file_handler = logging.FileHandler("bot.log", encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


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

        # Nettoyage downloads au démarrage
        from helper.cleanup import cleanup_all
        cleanup_all()

        # Serveur web (Web Service Render)
        if Config.WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", 8080).start()
            logger.info("🌐 Serveur web démarré sur le port 8080")

        logger.info(f"🤖 {me.first_name} démarré avec succès")

        for id in Config.ADMIN:
            try:
                await self.send_message(id, f"**{me.first_name} est démarré ✅**")
            except Exception as e:
                logger.warning(f"Impossible d'envoyer le message de démarrage à {id} : {e}")

        if Config.LOG_CHANNEL:
            try:
                curr     = datetime.now(timezone("Europe/Paris"))
                date     = curr.strftime('%d %B %Y')
                time_str = curr.strftime('%H:%M:%S')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} redémarré ✅**\n\n"
                    f"📅 Date : `{date}`\n"
                    f"⏰ Heure : `{time_str}`\n"
                    f"🌐 Fuseau : `Europe/Paris`\n\n"
                    f"🔧 Version : `v{__version__} (Layer {layer})`\n"
                    f"👨‍💻 Dev : @LabZero0 | 🛠 Prog : @Suayki"
                )
            except Exception as e:
                logger.warning(f"Impossible d'envoyer dans le canal log : {e}")


Bot().run()

# Développeur : LabZero — https://t.me/LabZero0
# Programmeur : Dev Suayki — https://t.me/Suayki
