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
    START_PIC   = os.environ.get("START_PIC", "")
    ADMIN       = [int(a) if id_pattern.search(a) else a
                   for a in os.environ.get("ADMIN", "").split()]
    FORCE_SUBS  = os.environ.get("FORCE_SUBS", "")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

    # Webhook : True sur Render (web service), False sur worker pur
    WEBHOOK     = bool(os.environ.get("WEBHOOK", False))


class Txt(object):
    START_TXT = """Hello {} 👋

➻ This Is An Advanced And Yet Powerful Rename Bot.

➻ Using This Bot You Can Rename And Change Thumbnail Of Your Files.

➻ You Can Also Convert Video To File And File To Video.

➻ This Bot Also Supports Custom Thumbnail And Custom Caption.

<b>Bot Is Made By :</b> @MadflixBotz"""

    ABOUT_TXT = """
╭───────────────⍟
├<b>🤖 My Name</b> : {}
├<b>🖥️ Developer</b> : <a href=https://t.me/MadflixBotz>MadflixBotz</a>
├<b>👨‍💻 Programer</b> : <a href=https://t.me/MadflixSupport>Jishu Developer</a>
├<b>📕 Library</b> : <a href=https://github.com/pyrogram>Pyrogram</a>
├<b>✏️ Language</b> : <a href=https://www.python.org>Python 3</a>
├<b>💾 Database</b> : <a href=https://supabase.com>Supabase (PostgreSQL)</a>
├<b>📊 Build Version</b> : <a href=https://instagram.com/jishukumarsinha>Rename v4.7.0</a></b>
╰───────────────⍟
"""

    HELP_TXT = """
🌌 <b><u>How To Set Thumbnail</u></b>

➪ /start - Start The Bot And Send Any Photo To Automatically Set Thumbnail.
➪ /del_thumb - Use This Command To Delete Your Old Thumbnail.
➪ /view_thumb - Use This Command To View Your Current Thumbnail.

📑 <b><u>How To Set Custom Caption</u></b>

➪ /set_caption - Use This Command To Set A Custom Caption
➪ /see_caption - Use This Command To View Your Custom Caption
➪ /del_caption - Use This Command To Delete Your Custom Caption
➪ Example - <code>/set_caption 📕 Name ➠ : {filename}
🔗 Size ➠ : {filesize}
⏰ Duration ➠ : {duration}</code>

✏️ <b><u>How To Rename A File</u></b>

➪ Send Any File And Type New File Name And Select The Format [ Document, Video, Audio ].

𝗔𝗻𝘆 𝗢𝘁𝗵𝗲𝗿 𝗛𝗲𝗹𝗽 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 :- <a href=https://t.me/MadflixSupport>Developer</a>
"""

    PROGRESS_BAR = """\n
<b>🔗 Size :</b> {1} | {2}
️ <b>⏳️ Done :</b> {0}%
<b>🚀 Speed :</b> {3}/s
️ <b>⏰️ ETA :</b> {4}
"""

    DONATE_TXT = """
<b>🥲 Thanks For Showing Interest In Donation! ❤️</b>

If You Like My Bots & Projects, You Can 🎁 Donate Me Any Amount From 10 Rs Upto Your Choice.

<b>🛍 UPI ID:</b> `kumarjishusinha@ibl`
"""

    SEND_METADATA = """<b><u>🖼️ HOW TO SET CUSTOM METADATA</u></b>

For Example :-

<code>By :- @MadflixBotz</code>

💬 For Any Help Contact @MadflixSupport
"""
