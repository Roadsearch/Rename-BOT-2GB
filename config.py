import os

class Config(object):
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    ADMIN = [int(admin) for admin in os.environ.get("ADMIN", "").split() if admin.isdigit()]
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0)) if os.environ.get("LOG_CHANNEL", "").replace("-", "").isdigit() else 0
    FORCE_SUB = os.environ.get("FORCE_SUB", "")
    START_PIC = os.environ.get("START_PIC", "https://unsplash.com")
    
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")

class Script(object):
    START_TXT = """<b>Salut {} !</b>\n\nBienvenue sur le bot avancé de renommage. Je peux renommer vos fichiers Telegram, modifier les métadonnées et y injecter une miniature permanente."""
    HELP_TXT = """<b>🛠️ Manuel d'Aide</b>\n\n1. Envoyez n'importe quelle photo au bot pour l'enregistrer comme miniature.\n2. Envoyez votre fichier ou vidéo.\n3. Entrez le nouveau nom avec son extension.\n4. Choisissez l'option d'envoi (Document ou Vidéo)."""
    ABOUT_TXT = """<b>💗 À Propos du Bot</b>\n\n• <b>Framework :</b> Pyrogram Async v2\n• <b>Database :</b> Supabase API\n• <b>Hébergeur :</b> Render Engine"""
