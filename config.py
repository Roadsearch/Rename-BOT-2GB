import os, time, re

id_pattern = re.compile(r'^.\d+$')

class Config(object):
    # Pyrogram client config
    API_ID    = int(os.environ.get("API_ID", "0"))
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # ── Supabase (remplace MongoDB) ──────────────────────────────────────
    # Récupère ces valeurs dans : Supabase → Project Settings → API
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")   # ex. https://xxxx.supabase.co
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")   # service_role key (pas anon)

    # ── Autres configs ───────────────────────────────────────────────────
    BOT_UPTIME  = time.time()
    ADMIN       = [int(a) if id_pattern.search(a) else a
                   for a in os.environ.get("ADMIN", "").split()]
    FORCE_SUBS  = os.environ.get("FORCE_SUBS", "")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

    # Webhook : True sur Render (web service), False sur worker pur
    WEBHOOK     = bool(os.environ.get("WEBHOOK", False))


class Txt(object):
    START_TXT = """Bonjour {} 👋

➻ Je suis un bot de renommage avancé et puissant.

➻ Tu peux renommer tes fichiers et modifier leur miniature.

➻ Tu peux aussi convertir une vidéo en fichier et vice-versa.

➻ Je supporte les miniatures personnalisées et les légendes personnalisées.

<b>Bot créé par :</b> <a href=https://t.me/LabZero0>LabZero</a>"""

    ABOUT_TXT = """
╭───────────────⍟
├<b>🤖 Nom</b> : {}
├<b>🖥️ Développeur</b> : <a href=https://t.me/LabZero0>LabZero</a>
├<b>👨‍💻 Programmeur</b> : <a href=https://t.me/Suayki>Dev Suayki</a>
├<b>📕 Bibliothèque</b> : <a href=https://github.com/pyrogram>Pyrogram</a>
├<b>✏️ Langage</b> : <a href=https://www.python.org>Python 3</a>
├<b>💾 Base de données</b> : <a href=https://supabase.com>Supabase (PostgreSQL)</a>
├<b>📊 Version</b> : Rename v4.7.0</b>
╰───────────────⍟
"""

    HELP_TXT = """
🌌 <b><u>Comment définir une miniature</u></b>

➪ /start — Démarre le bot, puis envoie une photo pour définir automatiquement la miniature.
➪ /del_thumb — Supprime ta miniature actuelle.
➪ /view_thumb — Affiche ta miniature actuelle.

📑 <b><u>Comment définir une légende personnalisée</u></b>

➪ /set_caption — Définir une légende personnalisée
➪ /see_caption — Voir ta légende actuelle
➪ /del_caption — Supprimer ta légende
➪ Exemple — <code>/set_caption 📕 Nom ➠ : {filename}
🔗 Taille ➠ : {filesize}
⏰ Durée ➠ : {duration}</code>

✏️ <b><u>Comment renommer un fichier</u></b>

➪ Envoie n'importe quel fichier, tape le nouveau nom, puis choisis le format [ Document, Vidéo, Audio ].

🔤 <b><u>Préfixe / Suffixe</u></b>

➪ /set_prefix — Définir un préfixe automatique
➪ /set_suffix — Définir un suffixe automatique

🔗 <b><u>Leech — Téléchargement direct</u></b>

➪ /leech <code>url</code> — Télécharge un lien direct (fichier, archive…)
➪ /ytdl <code>url</code> — YouTube, TikTok, Instagram, et 1000+ sites
➪ /ytdl <code>url</code> audio — Télécharge uniquement l'audio en MP3
📦 <b>Archives supportées :</b> zip, rar, 7z, tar, gz, bz2, xz

⏱️ <b><u>Auto-suppression</u></b>

➪ /autodelete — Choisir la durée avant suppression automatique des messages

📊 <b><u>Tes statistiques</u></b>

➪ /mystats — Voir tes préférences et ton nombre de fichiers traités

💬 Pour toute aide, contacte :- <a href=https://t.me/Suayki>Dev Suayki</a>
"""

    # PROGRESS_BAR supprimé — remplacé par helper/progress.py (ProgressUpdater)

    DONATE_TXT = """
<b>🥲 Merci pour ton intérêt ! ❤️</b>

Si tu aimes ce bot, n'hésite pas à contacter <a href=https://t.me/LabZero0>LabZero</a>.

<b>👨‍💻 Développeur :</b> <a href=https://t.me/LabZero0>LabZero</a>
<b>🛠 Programmeur :</b> <a href=https://t.me/Suayki>Dev Suayki</a>
"""

    SEND_METADATA = """<b><u>🖼️ COMMENT DÉFINIR DES MÉTADONNÉES PERSONNALISÉES</u></b>

Exemple :-

<code>Par :- @LabZero0</code>

💬 Pour toute aide, contacte <a href=https://t.me/Suayki>Dev Suayki</a>
"""
