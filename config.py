import os, time, re
id_pattern = re.compile(r'^.\d+$')



class Config(object):
    # pyro client config
    API_ID    = os.environ.get("API_ID", "")
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
   
    # database config (Supabase)
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
 
    # other configs
    BOT_UPTIME  = time.time()
    START_PIC   = os.environ.get("START_PIC", "")
    ADMIN = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '').split()]

    # channels logs
    FORCE_SUBS   = os.environ.get("FORCE_SUBS", "") 
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

    # wes response configuration     
    WEBHOOK = os.environ.get("WEBHOOK", "True").lower() == "true"



class Txt(object):
    # part of text configuration
    START_TXT = """Bonjour {} 👋 

➻ Ceci est un Bot de Renommage avancé et puissant.

➻ Grâce à ce Bot, vous pouvez renommer et changer la miniature de vos fichiers.

➻ Vous pouvez aussi convertir une Vidéo en Fichier et un Fichier en Vidéo.

➻ Ce Bot prend également en charge une miniature et une légende personnalisées.

<b>Bot Créé Par :</b> @LabZero0"""

    ABOUT_TXT = """
╭───────────────⍟
├<b>🤖 Mon Nom</b> : {}
├<b>🖥️ Channel dev</b> : <a href=https://t.me/LabZero0>LabZero</a> 
├<b>👨‍💻 Developer</b> : <a href=https://t.me/Suayki>Dev Suayki</a>
├<b>📕 Bibliothèque</b> : <a href=https://github.com/pyrogram>Pyrogram</a>
├<b>✏️ Langage</b> : <a href=https://www.python.org>Python 3</a>
├<b>💾 Base de données</b> : <a href=https://supabase.com>Supabase</a>
├<b>📊 Version</b> : <a href=https://t.me/LabZero0>Rename v4.7.0</a></b>     
╰───────────────⍟
"""

    HELP_TXT = """
🌌 <b><u>Comment Définir Une Miniature</u></b>
  
➪ /start - Démarrer le Bot et envoyer une Photo pour définir automatiquement la miniature.
➪ /del_thumb - Utilisez cette commande pour supprimer votre ancienne miniature.
➪ /view_thumb - Utilisez cette commande pour voir votre miniature actuelle.

📑 <b><u>Comment Définir Une Légende Personnalisée</u></b>

➪ /set_caption - Utilisez cette commande pour définir une légende personnalisée
➪ /see_caption - Utilisez cette commande pour voir votre légende personnalisée
➪ /del_caption - Utilisez cette commande pour supprimer votre légende personnalisée
➪ Exemple - <code>/set_caption 📕 Nom ➠ : {filename}

🔗 Taille ➠ : {filesize} 

⏰ Durée ➠ : {duration}</code>

✏️ <b><u>Comment Renommer Un Fichier</u></b>

➪ Envoyez n'importe quel fichier, tapez le nouveau nom de fichier et sélectionnez le format [ Document, Vidéo, Audio ].           

𝗣𝗼𝘂𝗿 𝗧𝗼𝘂𝘁𝗲 𝗔𝘂𝘁𝗿𝗲 𝗔𝗶𝗱𝗲, 𝗖𝗼𝗻𝘁𝗮𝗰𝘁𝗲𝘇 :- <a href=https://t.me/Suayki>Developer</a>
"""

    PROGRESS_BAR = """\n
 <b>🔗 Taille :</b> {1} | {2}
️ <b>⏳️ Terminé :</b> {0}%
 <b>🚀 Vitesse :</b> {3}/s
️ <b>⏰️ Temps restant :</b> {4}
"""

    DONATE_TXT = """
<b>🥲 Merci Pour Votre Intérêt À Faire Un Don ! ❤️</b>

Si Vous Aimez Mes Bots & Projets, Vous Pouvez 🎁 Me Faire Un Don De N'importe Quel Montant Selon Votre Choix.

<b>🛍 Contact :</b> <a href=https://t.me/Suayki>Dev Suayki</a>
"""


    SEND_METADATA = """<b><u>🖼️  COMMENT DÉFINIR DES MÉTADONNÉES PERSONNALISÉES</u></b>

Par Exemple :-

<code>Par :- @LabZero0</code>

💬 Pour Toute Aide, Contactez @Suayki
"""








# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
