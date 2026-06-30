"""
plugins/cookies.py
Gestion des cookies YouTube pour yt-dlp.
Admin envoie le fichier cookies.txt → stocké dans Supabase → utilisé par yt-dlp.

Comment exporter les cookies depuis Chrome/Firefox :
1. Installe l'extension "Get cookies.txt LOCALLY" (Chrome) ou "cookies.txt" (Firefox)
2. Va sur youtube.com en étant connecté à ton compte Google
3. Clique sur l'extension → Export → cookies.txt
4. Envoie ce fichier au bot avec la légende /setcookies
"""
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helper.database import set_bot_setting, get_bot_setting, del_bot_setting

logger       = logging.getLogger(__name__)
admin_filter = filters.user(Config.ADMIN)
COOKIES_PATH = "downloads/yt_cookies.txt"


async def get_cookies_path() -> str | None:
    """Retourne le chemin local du fichier cookies s'il existe."""
    stored = await get_bot_setting("yt_cookies")
    if stored and os.path.exists(COOKIES_PATH):
        return COOKIES_PATH
    return None


# ── /setcookies — envoyer le fichier cookies.txt ─────────────────────────────

@Client.on_message(
    filters.private & admin_filter
    & filters.document
    & filters.caption
    & filters.regex(r"^/setcookies")
)
async def setcookies_with_file(bot: Client, msg: Message):
    """Admin envoie cookies.txt avec la légende /setcookies."""
    fname = msg.document.file_name or ""
    if not fname.endswith(".txt"):
        await msg.reply_text(
            "❌ **Fichier invalide.**\n\n"
            "Envoie un fichier `.txt` (format Netscape cookies)."
        )
        return

    status = await msg.reply_text("⬇️ **Téléchargement des cookies...**")
    try:
        os.makedirs("downloads", exist_ok=True)
        path = await bot.download_media(
            msg.document.file_id,
            file_name=COOKIES_PATH
        )
        # Vérifie que c'est bien un fichier cookies Netscape
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if "Netscape" not in first_line and "# HTTP" not in first_line:
            os.remove(path)
            await status.edit_text(
                "❌ **Format invalide.**\n\n"
                "Le fichier doit être au format Netscape cookies.\n"
                "Utilise l'extension **Get cookies.txt LOCALLY**."
            )
            return

        # Compte les entrées YouTube
        with open(path, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if "youtube.com" in l or "google.com" in l]

        await set_bot_setting("yt_cookies", "active")
        logger.info(f"[Cookies] Défini par {msg.from_user.id} — {len(lines)} entrées YT/Google")

        await status.edit_text(
            f"✅ **Cookies YouTube enregistrés !**\n\n"
            f"📋 **Entrées YouTube/Google :** `{len(lines)}`\n\n"
            f"yt-dlp utilisera ces cookies pour contourner la restriction.\n"
            f"**Durée de validité :** ~30 jours (renouvelle si yt-dlp échoue à nouveau)\n\n"
            f"Pour supprimer : `/delcookies`"
        )
    except Exception as e:
        logger.error(f"[Cookies] Erreur : {e}")
        await status.edit_text(f"❌ **Erreur :** `{e}`")


# ── /setcookies seul sans fichier ────────────────────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("setcookies"))
async def setcookies_help(bot: Client, msg: Message):
    if msg.document:
        return
    await msg.reply_text(
        "🍪 **Comment configurer les cookies YouTube :**\n\n"
        "**Étape 1 — Installer l'extension**\n"
        "Chrome : *Get cookies.txt LOCALLY*\n"
        "Firefox : *cookies.txt*\n\n"
        "**Étape 2 — Exporter les cookies**\n"
        "1. Va sur youtube.com **connecté** à ton compte Google\n"
        "2. Clique sur l'extension\n"
        "3. Sélectionne **Export** → `cookies.txt`\n\n"
        "**Étape 3 — Envoyer au bot**\n"
        "Envoie le fichier `cookies.txt` avec la légende `/setcookies`\n\n"
        "⚠️ Les cookies expirent environ tous les **30 jours**."
    )


# ── /viewcookies ─────────────────────────────────────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("viewcookies"))
async def viewcookies_cmd(bot: Client, msg: Message):
    stored = await get_bot_setting("yt_cookies")
    if not stored:
        await msg.reply_text("❌ **Aucun cookie défini.**\n\nUtilise `/setcookies` pour en ajouter.")
        return

    exists = os.path.exists(COOKIES_PATH)
    count  = 0
    if exists:
        with open(COOKIES_PATH, "r", encoding="utf-8") as f:
            count = sum(1 for l in f if "youtube.com" in l or "google.com" in l)

    await msg.reply_text(
        f"🍪 **Statut des cookies YouTube**\n\n"
        f"📁 **Fichier :** {'✅ Présent' if exists else '❌ Manquant (redéploie)'}\n"
        f"📋 **Entrées YT/Google :** `{count}`\n\n"
        f"Si yt-dlp échoue encore, renouvelle les cookies avec `/setcookies`."
    )


# ── /delcookies ──────────────────────────────────────────────────────────────

@Client.on_message(filters.private & admin_filter & filters.command("delcookies"))
async def delcookies_cmd(bot: Client, msg: Message):
    await del_bot_setting("yt_cookies")
    if os.path.exists(COOKIES_PATH):
        os.remove(COOKIES_PATH)
        logger.info(f"[Cookies] Supprimés par {msg.from_user.id}")
    await msg.reply_text("🗑️ **Cookies supprimés.** yt-dlp fonctionnera sans cookies.")
