import os
import sys
import time
import math
import random
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from supabase import create_client, Client as SupabaseClient
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config

# --- CONFIGURATION & LOGS ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "./downloads"
DEFAULT_THUMBS_DIR = "./default_thumbs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DEFAULT_THUMBS_DIR, exist_ok=True)

config.quiet = True 
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2 Go

# --- VARIABLES D'ENVIRONNEMENT ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN = int(os.environ.get("ADMIN", 0))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Nouveautés : Force Sub
FSUB_CHANNEL_1 = os.environ.get("FSUB_CHANNEL_1", "") # ID ou Username du canal 1 (ex: -100123456789)
FSUB_CHANNEL_2 = os.environ.get("FSUB_CHANNEL_2", "")
FSUB_LINK_1 = os.environ.get("FSUB_LINK_1", "https://t.me/TonCanal1")
FSUB_LINK_2 = os.environ.get("FSUB_LINK_2", "https://t.me/TonCanal2")

START_PIC = os.environ.get("START_PIC", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500")

# --- INITIALISATION ---
bot = Client("AdvancedRenamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=24)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variables globales
user_data = {}
cancelled_tasks = set()
task_queue = asyncio.Queue()
is_processing = False
last_update_times = {}

# --- FONCTION FORCE SUB (ABONNEMENT OBLIGATOIRE) ---
async def check_fsub(client, message):
    user_id = message.from_user.id
    if user_id == ADMIN:
        return True
        
    not_joined = []
    if FSUB_CHANNEL_1:
        try:
            await client.get_chat_member(FSUB_CHANNEL_1, user_id)
        except UserNotParticipant:
            not_joined.append((FSUB_LINK_1, "🔺 CANAL DE MISES A JOURS 1 🔺"))
        except Exception: pass

    if FSUB_CHANNEL_2:
        try:
            await client.get_chat_member(FSUB_CHANNEL_2, user_id)
        except UserNotParticipant:
            not_joined.append((FSUB_LINK_2, "🔺 CANAL DE MISES A JOURS 2 🔺"))
        except Exception: pass

    if not_joined:
        buttons = [[InlineKeyboardButton(name, url=link)] for link, name in not_joined]
        text = f"**BONJOUR {message.from_user.first_name},**\n\n**VOUS DEVEZ REJOINDRE MON CANAL POUR M'UTILISER.**\n\n**VEUILLEZ REJOINDRE LE CANAL.**"
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return False
    return True

# --- UTILITAIRES ---
async def register_user(user_id):
    """Enregistre l'utilisateur en base de données pour les statistiques et le broadcast"""
    try:
        await asyncio.to_thread(lambda: supabase.table("users").upsert({"user_id": user_id}).execute())
    except Exception as e:
        logger.error(f"Erreur DB User: {e}")

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

async def progress_bar(current, total, reply_msg, text, start_time, mode, user_id):
    if user_id in cancelled_tasks:
        raise Exception("USER_CANCELLED_TASK")

    if not total or total == 0: return
        
    now = time.time()
    msg_id = reply_msg.id
    last_update = last_update_times.get(msg_id, 0)
    
    if (now - last_update) < 3.5 and current != total:
        return

    last_update_times[msg_id] = now
    diff = now - start_time
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = round((total - current) / speed) if speed > 0 else 0
    eta_str = f"{eta}s" if eta < 60 else f"{eta//60}m {eta%60}s"
    
    completed_blocks = math.floor(percentage / 5)
    bar = "■" * completed_blocks + "□" * (20 - completed_blocks)
    
    progress_text = (
        f"{text}\n\n"
        f"{bar}\n\n"
        f"🔗 **Size :** {current / (1024*1024):.1f} MB | {total / (1024*1024):.2f} MB\n"
        f"⏳ **Done :** {percentage:.2f}%\n"
        f"🚀 **Speed :** {speed / (1024 * 1024):.2f} MB/s\n"
        f"⏰ **ETA :** {eta_str}"
    )
        
    try:
        await reply_msg.edit(progress_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Task ✖️", callback_data="cancel_action")]]))
    except: pass
        
    if current == total and msg_id in last_update_times:
        last_update_times.pop(msg_id, None)

# --- COMMANDES UTILISATEURS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if not await check_fsub(client, message): return
    await register_user(message.from_user.id)
    
    buttons = [
        [InlineKeyboardButton("📢 Updates", url=FSUB_LINK_1), InlineKeyboardButton("💬 Support", url="https://t.me/TonSupport")],
        [InlineKeyboardButton("🛠️ Help", callback_data="help_panel"), InlineKeyboardButton("💗 About", callback_data="about_panel")],
        [InlineKeyboardButton("🧑‍💻 Developer 🧑‍💻", url="https://t.me/DevSuayki")]
    ]
    welcome_text = f"Hey **{message.from_user.first_name}**\n\nWelcome To Our MadflixBotz Community Bot. Exclusively Work For MadflixBotz !!\n\n4GB Renamer, VIP Experience"
    try: await message.reply_photo(photo=START_PIC, caption=welcome_text, reply_markup=InlineKeyboardMarkup(buttons))
    except: await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

# --- COMMANDES ADMIN ---
@bot.on_message(filters.command("ping"))
async def ping_cmd(client, message):
    start_t = time.time()
    msg = await message.reply_text("⚡ Ping...")
    end_t = time.time()
    await msg.edit(f"**Pong !** 🏓\nLatence : `{round((end_t - start_t) * 1000)}ms`")

@bot.on_message(filters.command("users") & filters.user(ADMIN))
async def users_cmd(client, message):
    try:
        res = await asyncio.to_thread(lambda: supabase.table("users").select("user_id", count="exact").execute())
        count = res.count if res.count else 0
        await message.reply_text(f"📊 **Statistiques :**\n\n👥 Nombre total d'utilisateurs : `{count}`")
    except Exception as e:
        await message.reply_text(f"❌ Erreur : {e}")

@bot.on_message(filters.command("logs") & filters.user(ADMIN))
async def logs_cmd(client, message):
    if os.path.exists("bot.log"):
        await message.reply_document("bot.log", caption="📝 **Voici les logs récents du bot.**")
    else:
        await message.reply_text("❌ **Aucun fichier de log trouvé.**")

@bot.on_message(filters.command("restart") & filters.user(ADMIN))
async def restart_cmd(client, message):
    await message.reply_text("🔄 **Redémarrage en cours...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("broadcast") & filters.user(ADMIN) & filters.reply)
async def broadcast_cmd(client, message):
    msg_to_send = message.reply_to_message
    res = await asyncio.to_thread(lambda: supabase.table("users").select("user_id").execute())
    users = res.data if res.data else []
    
    success, failed = 0, 0
    b_msg = await message.reply_text(f"📢 **Diffusion en cours à {len(users)} utilisateurs...**")
    
    for user in users:
        try:
            await msg_to_send.copy(chat_id=user["user_id"])
            success += 1
            await asyncio.sleep(0.1) # Anti-flood
        except:
            failed += 1
            
    await b_msg.edit(f"✅ **Diffusion Terminée !**\n\n🎯 Réussis : `{success}`\n🚫 Échoués : `{failed}`")

# --- RÉCEPTION MÉDIA (FORMAT IDENTIQUE AUX SCREENS) ---
@bot.on_message((filters.document | filters.video) & filters.private)
async def receive_file(client, message):
    if not await check_fsub(client, message): return
    await register_user(message.from_user.id)
    
    user_id = message.from_user.id
    file = message.document or message.video
    
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ File size exceeds 2GB limit.")
        return
        
    orig_ext = os.path.splitext(file.file_name)[1] if file.file_name else ".mp4"
    user_data[user_id] = {
        "file_id": file.file_id,
        "original_name": file.file_name or f"video_{user_id}.mp4",
        "orig_ext": orig_ext if orig_ext else ".mp4"
    }
    
    info_text = (
        f"**QUE SHOUAITEZ-VOUS FAIRE AVEC CE FICHIER?**\n\n"
        f"**NOM DU FILE :-** `{file.file_name}`\n"
        f"**TAILLE DU FILE :-** {file.file_size / (1024*1024):.1f} MB\n"
        f"**ID DC :-** {getattr(file, 'dc_id', '4')}"
    )
    buttons = [
        [InlineKeyboardButton("📝 RENOMMER", callback_data="trigger_rename"), InlineKeyboardButton("✖️ ANNULER", callback_data="cancel_action")]
    ]
    await message.reply_text(info_text, reply_markup=InlineKeyboardMarkup(buttons))

# --- CALLBACKS & TEXT INPUT ---
@bot.on_callback_query(filters.regex("^(trigger_rename|cancel_action|help_panel|about_panel)$"))
async def handle_callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "cancel_action":
        cancelled_tasks.add(user_id)
        user_data.pop(user_id, None)
        await callback_query.message.edit("❌ **Task Cancelled Successfully.**")
    elif data == "trigger_rename":
        if user_id not in user_data:
            await callback_query.answer("❌ Session Expired.", show_alert=True)
            return
        await callback_query.message.edit("📝 **Please reply to this message with the new filename.**\n\n_Note: Extension is not required._")
        user_data[user_id]["awaiting_name"] = True

@bot.on_message(filters.text & filters.private & ~filters.command(["start", "help", "settings", "viewthumb", "delthumb", "set_caption", "see_caption", "del_caption", "ping", "users", "logs", "restart", "broadcast"]))
async def process_text_input(client, message):
    if not await check_fsub(client, message): return
    user_id = message.from_user.id
    
    if user_id not in user_data or not user_data[user_id].get("awaiting_name"): return
    
    input_name = message.text.strip()
    orig_ext = user_data[user_id]["orig_ext"]
    final_name = input_name if input_name.endswith(orig_ext) else f"{input_name}{orig_ext}"
        
    user_data[user_id]["new_name"] = final_name
    user_data[user_id]["awaiting_name"] = False
    
    text = f"**Select The Output File Type**\n\n**File Name :-** `{final_name}`"
    buttons = [[InlineKeyboardButton("📁 Document", callback_data="queue|doc"), InlineKeyboardButton("🎥 Video", callback_data="queue|video")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- FILE D'ATTENTE & TÉLÉCHARGEMENT ---
@bot.on_callback_query(filters.regex("^queue"))
async def add_to_queue(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data or "new_name" not in user_data[user_id]:
        await callback_query.answer("❌ Session Error.", show_alert=True)
        return

    cancelled_tasks.discard(user_id)
    await task_queue.put((callback_query, user_id))
    await callback_query.message.edit(f"⏳ **Added to queue...**\n📍 Position : `{task_queue.qsize()}`")
    asyncio.create_task(process_queue(client))

async def process_queue(client):
    global is_processing
    if is_processing: return
    is_processing = True
    
    while not task_queue.empty():
        callback_query, user_id = await task_queue.get()
        final_path, thumb_file = None, None
        
        try:
            file_info = user_data.get(user_id)
            if not file_info or user_id in cancelled_tasks: continue
            
            upload_type = callback_query.data.split("|")[1]
            new_name = file_info["new_name"]
            
            msg = await callback_query.message.edit("🚀 ⚡ **Initialisation...** ⚡\n\n□□□□□□□□□□□□□□□□□□□□\n\n🔗 **Size :** 0.0 MB | -- MB")
            start_time = time.time()
            custom_download_path = os.path.join(DOWNLOAD_DIR, file_info["original_name"])
            
            download_path = await client.download_media(
                message=file_info["file_id"], file_name=custom_download_path,
                progress=progress_bar,
                progress_args=(msg, "🚀 **Downloading Media...** ⚡", start_time, "download", user_id)
            )
            
            if not download_path or user_id in cancelled_tasks: continue

            final_path = os.path.join(DOWNLOAD_DIR, new_name)
            os.rename(download_path, final_path)
            
            # Paramètres et Miniature
            res = await asyncio.to_thread(lambda: supabase.table("bot_settings").select("*").eq("user_id", user_id).execute())
            settings = res.data[0] if res.data else {}
            
            if settings.get("thumbnail_file_id"):
                thumb_file = await client.download_media(message=settings["thumbnail_file_id"], file_name=os.path.join(DOWNLOAD_DIR, f"t_{user_id}.jpg"))
            
            duration, width, height = get_video_metadata(final_path)
            
            custom_caption = settings.get("custom_caption", f"🎥 **Fichier :** `{new_name}`")
            if "{filename}" in custom_caption: custom_caption = custom_caption.replace("{filename}", new_name)

            start_upload_time = time.time()
            dump_target = settings.get("dump_channel_id", user_id)
            
            if upload_type == "video":
                await client.send_video(
                    chat_id=dump_target, video=final_path, caption=custom_caption, thumb=thumb_file,
                    duration=duration, width=width, height=height, supports_streaming=True,
                    progress=progress_bar, progress_args=(msg, "📤 **Uploading Video...** ⚡", start_upload_time, "upload", user_id)
                )
            else:
                await client.send_document(
                    chat_id=dump_target, document=final_path, caption=custom_caption, thumb=thumb_file,
                    progress=progress_bar, progress_args=(msg, "📤 **Uploading Document...** ⚡", start_upload_time, "upload", user_id)
                )
            
            if dump_target != user_id:
                await client.send_message(chat_id=user_id, text=f"🚀 **File successfully processed and sent to your Dump Channel !**")
            await msg.delete()

        except Exception as e:
            if "USER_CANCELLED_TASK" not in str(e): logger.error(f"Erreur d'exécution: {e}")
        finally:
            if final_path and os.path.exists(final_path): os.remove(final_path)
            if thumb_file and os.path.exists(thumb_file) and DOWNLOAD_DIR in thumb_file: os.remove(thumb_file)
            user_data.pop(user_id, None)
            cancelled_tasks.discard(user_id)
            task_queue.task_done()
            
    is_processing = False

if __name__ == "__main__":
    import http.server, threading
    class DummyServer(http.server.SimpleHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Ready")
    threading.Thread(target=lambda: http.server.HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), DummyServer).serve_forever(), daemon=True).start()
    bot.run()
