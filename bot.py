import os
import sys
import time
import math
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.methods.utilities.idle import idle
from pyrogram.errors import UserNotParticipant, FloodWait
from supabase import create_async_client, AsyncClient as SupabaseAsyncClient
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config as hachoir_config
from config import Config, Script

# --- CONFIGURATION INITIALE & LOGS ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
hachoir_config.quiet = True

# --- INITIALISATION DES CLIENTS GLOBAUX ---
bot = Client("RenameBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN, workers=24)
supabase: SupabaseAsyncClient = None

# Gestionnaires d'état en mémoire vive
user_data = {}
cancelled_tasks = set()
task_queue = asyncio.Queue()
is_processing = False
last_update_times = {}

# --- FILTRES & SÉCURITÉ ---
def is_admin_filter(filter, client, message):
    return message.from_user and message.from_user.id in Config.ADMIN

admin_filter = filters.create(is_admin_filter)

async def check_fsub(client, message):
    if not Config.FORCE_SUB: return True
    user_id = message.from_user.id
    if user_id in Config.ADMIN: return True
    try:
        await client.get_chat_member(Config.FORCE_SUB, user_id)
        return True
    except UserNotParticipant:
        btn = [[InlineKeyboardButton("🔺 Rejoindre le Canal 🔺", url=f"https://t.me/{Config.FORCE_SUB.replace('@', '')}")]]
        await message.reply_text("<b>Accès Refusé !</b>\n\nVous devez rejoindre notre canal pour utiliser ce bot.", reply_markup=InlineKeyboardMarkup(btn))
        return False
    except Exception:
        return True

async def check_vip_status(user_id):
    if user_id in Config.ADMIN: return True
    try:
        res = await supabase.table("users").select("is_vip").eq("user_id", user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0].get("is_vip", False)
    except Exception as e:
        logger.error(f"Erreur vérification VIP: {e}")
    return False

async def register_user(user_id):
    try:
        await supabase.table("users").upsert({"user_id": user_id}).execute()
    except Exception as e:
        logger.error(f"Erreur DB registration: {e}")

# --- TRANSFERTS SÉCURISÉS & NETTOYAGE ---
async def safe_telegram_send(client, method, **kwargs):
    try:
        return await getattr(client, method)(**kwargs)
    except FloodWait as e:
        logger.warning(f"[FLOOD] Attente requise de {e.value}s")
        await asyncio.sleep(e.value)
        return await safe_telegram_send(client, method, **kwargs)

def clean_local_storage(user_id, download_path, thumb_path):
    try:
        if download_path and os.path.exists(download_path): os.remove(download_path)
        if thumb_path and os.path.exists(thumb_path) and Config.DOWNLOAD_DIR in thumb_path: os.remove(thumb_path)
    except Exception as e:
        logger.error(f"Erreur nettoyage stockage : {e}")

async def send_log_to_channel(client, user_id, first_name, file_name, file_size, action_status, error_msg=None):
    if not Config.LOG_CHANNEL: return
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = "✅ SUCCÈS" if action_status == "SUCCESS" else ("✖️ ANNULÉ" if action_status == "CANCELLED" else "🚨 ÉCHEC")
    details = f"📝 **Nouveau nom :** `{file_name}`" if action_status == "SUCCESS" else (f"❌ **Interrompu par l'utilisateur.**" if action_status == "CANCELLED" else f"⚠️ **Raison :** `{error_msg}`")

    log_text = (
        f"📋 **RAPPORT DE RENOMMAGE** | {status_emoji}\n\n"
        f"👤 **Utilisateur :** {first_name} [ `{user_id}` ]\n"
        f"📅 **Date :** `{current_time}`\n"
        f"📂 **Fichier :** `{file_name}`\n"
        f"⚖️ **Taille :** `{file_size / (1024*1024):.2f} MB`\n\n"
        f"{details}"
    )
    try: await client.send_message(chat_id=Config.LOG_CHANNEL, text=log_text)
    except Exception as e: logger.error(f"Erreur envoi log : {e}")

# --- BARRE DE PROGRESSION ---
def progress_bar(current, total, reply_msg, text, start_time, mode, user_id):
    if user_id in cancelled_tasks: raise Exception("USER_CANCELLED_TASK")
    if not total: return
    now = time.time()
    msg_id = reply_msg.id
    if (now - last_update_times.get(msg_id, 0)) < 3.5 and current != total: return
    last_update_times[msg_id] = now
    position = task_queue.qsize()
    asyncio.get_event_loop().create_task(build_progress_text(current, total, reply_msg, text, start_time, user_id, position))

async def build_progress_text(current, total, reply_msg, text, start_time, user_id, position):
    now = time.time()
    diff = now - start_time
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = round((total - current) / speed) if speed > 0 else 0
    eta_str = f"{eta}s" if eta < 60 else f"{eta//60}m {eta%60}s"
    bar = "▣" * math.floor(percentage / 5) + "▢" * (20 - math.floor(percentage / 5))
    queue_text = f"📍 **Position dans la file :** `En cours...`" if position == 0 else f"⏳ **Fichiers en attente :** `{position}`"
    progress_template = (
        f"<b>{text}</b>\n\n<code>{bar}</code>\n\n"
        f" 🔗 **Size :** {current / (1024*1024):.1f} MB | {total / (1024*1024):.2f} MB\n"
        f"️ ⏳️ **Done :** {percentage:.2f}%\n"
        f" 🚀 **Speed :** {speed / (1024 * 1024):.2f} MB/s\n"
        f"️ ⏰️ **ETA :** {eta_str}\n\n{queue_text}"
    )
    try: await reply_msg.edit(text=progress_template, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Task ✖️", callback_data="cancel_action")]]))
    except: pass

def get_video_metadata(file_path):
    duration, width, height = 0, 0, 0
    try:
        parser = createParser(file_path)
        if parser:
            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    if metadata.has("duration"): duration = int(metadata.get("duration").seconds)
                    if metadata.has("width"): width = int(metadata.get("width"))
                    if metadata.has("height"): height = int(metadata.get("height"))
    except: pass
    return duration, width, height

# --- RECEPTION ET COMMANDES ---
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await check_fsub(client, message): return
    await register_user(message.from_user.id)
    buttons = [[InlineKeyboardButton("🛠️ Aide", callback_data="help"), InlineKeyboardButton("💗 À Propos", callback_data="about")]]
    await message.reply_photo(photo=Config.START_PIC, caption=Script.START_TXT.format(message.from_user.first_name), reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query()
async def callback_handler(client, query):
    user_id = query.from_user.id
    if query.data == "help": await query.message.edit_text(Script.HELP_TXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour", callback_data="back")]]))
    elif query.data == "about": await query.message.edit_text(Script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Retour", callback_data="back")]]))
    elif query.data == "back": await query.message.edit_text(Script.START_TXT.format(query.from_user.first_name), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Aide", callback_data="help"), InlineKeyboardButton("💗 À Propos", callback_data="about")]]))
    elif query.data == "cancel_action":
        cancelled_tasks.add(user_id)
        await query.answer("Annulation prise en compte...", show_alert=True)
    elif query.data.startswith("queue"):
        if user_id not in user_data or "new_name" not in user_data[user_id]:
            await query.answer("❌ Erreur de session.", show_alert=True)
            return
        upload_type = query.data.split("|")[1]
        await task_queue.put((query, user_id, upload_type))
        await query.message.edit(f"⏳ **Ajouté à la file d'attente...**\n📍 Position : `{task_queue.qsize()}`")

@bot.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_media(client, message):
    if not await check_fsub(client, message): return
    user_id = message.from_user.id
    media = getattr(message, message.media.value)
    is_vip = await check_vip_status(user_id)
    limit_size = 4000 * 1024 * 1024 if is_vip else 2000 * 1024 * 1024
    if media.file_size > limit_size:
        await message.reply_text(f"❌ Fichier trop lourd (Limite : {'4 Go' if is_vip else '2 Go'}).")
        return
    user_data[user_id] = {"file_id": media.file_id, "original_name": media.file_name or "file", "file_size": media.file_size}
    await message.reply_text(f"📂 **Fichier détecté :** `{media.file_name}`\n✏️ Envoyez le nouveau nom complet.")

@bot.on_message(filters.private & filters.text & ~filters.command(["start","addvip","delvip","status","set_prefix","set_suffix","set_caption"]))
async def process_rename(client, message):
    user_id = message.from_user.id
    if user_id not in user_data or "file_id" not in user_data[user_id]: return
    user_data[user_id]["new_name"] = message.text.strip()
    buttons = [[InlineKeyboardButton("🎥 Vidéo", callback_data="queue|video"), InlineKeyboardButton("📁 Document", callback_data="queue|document")]]
    await message.reply_text("Choisissez le format d'envoi final :", reply_markup=InlineKeyboardMarkup(buttons))

# --- GESTIONNAIRE DE FILE D'ATTENTE UNIQUE ---
async def queue_processing_core(client):
    global is_processing
    while True:
        query, user_id, upload_type = await task_queue.get()
        is_processing = True
        final_path, thumb_file = None, None
        try:
            info = user_data.get(user_id)
            if not info or user_id in cancelled_tasks: continue
            msg = await query.message.edit("🚀 ⚡ Initialisation... ⚡")
            start_time = time.time()
            download_path = await client.download_media(
                message=info["file_id"], file_name=os.path.join(Config.DOWNLOAD_DIR, info["original_name"]),
                progress=progress_bar, progress_args=(msg, "🚀 Downloading...", start_time, "download", user_id)
            )
            if not download_path or user_id in cancelled_tasks: continue
            res = await supabase.table("bot_settings").select("*").eq("user_id", user_id).execute()
            settings = res.data[0] if res.data else {}
            prefix = settings.get("prefix", "")
            suffix = settings.get("suffix", "")
            file_root, file_ext = os.path.splitext(info["new_name"])
            processed_name = f"{prefix} {file_root} {suffix}".strip() + file_ext
            processed_name = " ".join(processed_name.split())
            final_path = os.path.join(Config.DOWNLOAD_DIR, processed_name)
            os.rename(download_path, final_path)
            
            if settings.get("thumbnail_file_id"):
                thumb_file = await client.download_media(message=settings["thumbnail_file_id"], file_name=os.path.join(Config.DOWNLOAD_DIR, f"t_{user_id}.jpg"))
            
            duration, width, height = get_video_metadata(final_path)
            caption = settings.get("custom_caption", f"🎥 Fichier : {processed_name}")
            if "{filename}" in caption: caption = caption.replace("{filename}", processed_name)
            
            await msg.edit("🚀 Envoi en cours... ⚡️")
            send_payload = {"chat_id": user_id, "caption": caption, "thumb": thumb_file, "progress": progress_bar, "progress_args": (msg, "🚀 Uploading...", time.time(), "upload", user_id)}
            
            if upload_type == "video":
                send_payload.update({"video": final_path, "duration": duration, "width": width, "height": height, "supports_streaming": True})
                await safe_telegram_send(client, "send_video", **send_payload)
            else:
                send_payload.update({"document": final_path})
                await safe_telegram_send(client, "send_document", **send_payload)
            
            await msg.delete()
            await send_log_to_channel(client, user_id, query.from_user.first_name, processed_name, info["file_size"], "SUCCESS")
        except Exception as e:
            logger.error(f"Erreur d'exécution: {e}")
        finally:
            clean_local_storage(user_id, final_path, thumb_file)
            user_data.pop(user_id, None)
            cancelled_tasks.discard(user_id)
            task_queue.task_done()
            is_processing = False

# --- COMMANDES CONFIGURATION ---
@bot.on_message(filters.command("set_prefix") & filters.private)
async def set_prefix(c, m):
    if len(m.command) < 2: return await m.reply_text("❌ Usage: /set_prefix [Texte]")
    await supabase.table("bot_settings").upsert({"user_id": m.from_user.id, "prefix": m.text.split(" ", 1)[1].strip()}).execute()
    await m.reply_text("✅ Préfixe configuré.")

@bot.on_message(filters.command("set_suffix") & filters.private)
async def set_suffix(c, m):
    if len(m.command) < 2: return await m.reply_text("❌ Usage: /set_suffix [Texte]")
    await supabase.table("bot_settings").upsert({"user_id": m.from_user.id, "suffix": m.text.split(" ", 1)[1].strip()}).execute()
    await m.reply_text("✅ Suffixe configuré.")

@bot.on_message(filters.command("set_caption") & filters.private)
async def set_caption(c, m):
    if len(m.command) < 2: return await m.reply_text("❌ Usage: /set_caption [Texte]")
    await supabase.table("bot_settings").upsert({"user_id": m.from_user.id, "custom_caption": m.text.split(" ", 1)[1].strip()}).execute()
    await m.reply_text("✅ Légende configurée.")

@bot.on_message(filters.private & filters.photo)
async def save_thumb(c, m):
    await supabase.table("bot_settings").upsert({"user_id": m.from_user.id, "thumbnail_file_id": m.photo.file_id}).execute()
    await m.reply_text("💾 Miniature sauvegardée.")

# --- MODULE ADMINISTRATEUR ---
@bot.on_message(filters.command("addvip") & admin_filter)
async def add_vip(c, m):
    if len(m.command) < 2: return await m.reply_text("❌ Usage: /addvip [user_id]")
    await supabase.table("users").upsert({"user_id": int(m.command[1]), "is_vip": True}).execute()
    await m.reply_text("👑 Utilisateur promu VIP.")

@bot.on_message(filters.command("status") & admin_filter)
async def status(c, m):
    res = await supabase.table("users").select("user_id", count="exact").execute()
    await m.reply_text(f"📊 Membres : {res.count or 0}\n⏳ File : {task_queue.qsize()}")

# --- SERVEUR KEEP-ALIVE ---
async def start_render_ping_server():
    from aiohttp import web
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot Operational"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()

async def main():
    global supabase
    supabase = await create_async_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    await start_render_ping_server()
    await bot.start()
    asyncio.create_task(queue_processing_core(bot))
    await idle()
    await bot.stop()

if __name__ == "__main__":
    bot.run(main())
