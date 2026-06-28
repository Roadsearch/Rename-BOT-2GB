import os
import time
import math
import random
import asyncio
import httpx
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client as SupabaseClient
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from hachoir.core import config

# Configuration des dossiers
DOWNLOAD_DIR = "./downloads"
DEFAULT_THUMBS_DIR = "./default_thumbs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DEFAULT_THUMBS_DIR, exist_ok=True)

# Désactive les logs verbeux de Hachoir pour éviter de saturer Render
config.quiet = True 

MAX_FILE_SIZE = 2000 * 1024 * 1024  # Limite de 2 Go

# Variables d'environnement
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN = int(os.environ.get("ADMIN", 0))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", ADMIN))
START_PIC = os.environ.get("START_PIC", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500")

# --- INITIALISATION DES CLIENTS (CORRIGÉ POUR HTTPX/SUPABASE) ---
bot = Client(
    "AdvancedRenamer",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=24  # Accélération des requêtes réseau en parallèle
)

# Correction majeure : Injection propre du client httpx compatible
with httpx.Client(timeout=30.0) as client:
    supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

user_data = {}
task_queue = asyncio.Queue()
is_processing = False

# Dictionnaire global pour un anti-flood strict par ID de message
last_update_times = {}

# --- UTILS & METADONNÉES ---
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

async def progress_bar(current, total, reply_msg, text, start_time, mode="download"):
    if not total or total == 0: 
        return
        
    now = time.time()
    msg_id = reply_msg.id
    last_update = last_update_times.get(msg_id, 0)
    
    # Limitation temporelle : rafraîchissement toutes les 3.5s maximum (sauf si complété)
    if (now - last_update) < 3.5 and current != total:
        return

    last_update_times[msg_id] = now
    
    diff = now - start_time
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    eta = round((total - current) / speed) if speed > 0 else 0
    eta_str = f"{eta}s" if eta < 60 else f"{eta//60}m {eta%60}s"
    
    if mode == "download":
        completed_blocks = math.floor(percentage / 5)
        bar = "▣" * completed_blocks + "▢" * (20 - completed_blocks)
        
        progress_text = (
            f"{text}\n\n"
            f"{bar}\n\n"
            f" 🔗 **Size :** {current / (1024*1024):.1f} MB | {total / (1024*1024):.1f} MB\n"
            f"️ ⏳️ **Done :** {percentage:.2f}%\n"
            f" 🚀 **Speed :** {speed / (1024 * 1024):.2f} MB/s\n"
            f"️ ⏰️ **ETA :** {eta_str}"
        )
    else:
        completed_blocks = math.floor(percentage / 6)
        bar = "█" * completed_blocks + "░" * (17 - completed_blocks)
        
        progress_text = (
            f"{text}\n\n"
            f"|{bar}| {percentage:.2f}%\n"
            f"📦 **Size :** {current / (1024*1024):.1f} / {total / (1024*1024):.1f} Mo\n"
            f"⏳️ **Done :** {percentage:.2f}%\n"
            f"🚀 **Speed :** {speed / (1024 * 1024):.2f} Mo/s\n"
            f"⏳ **ETA :** {eta_str}"
        )
        
    try:
        await reply_msg.edit(
            progress_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Task ✖️", callback_data="cancel_action")]])
        )
    except: 
        pass
        
    if current == total and msg_id in last_update_times:
        try: del last_update_times[msg_id]
        except: pass

# --- COMMANDES PRINCIPALES ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = [
        [InlineKeyboardButton("📢 Updates", url="https://t.me/MonCanalUpdates"), InlineKeyboardButton("💬 Support", url="https://t.me/MonContactSupport")],
        [InlineKeyboardButton("🛠️ Help", callback_data="help_panel"), InlineKeyboardButton("💗 About", callback_data="about_panel")],
        [InlineKeyboardButton("🧑‍💻 Developer 🧑‍💻", url="https://t.me/DevSuayki")]
    ]
    welcome_text = f"Hey **{message.from_user.first_name}**\n\nWelcome To Our MadflixBotz Community Bot. Exclusively Work For MadflixBotz !!\n\n4GB Renamer, VIP Experience"
    try: await message.reply_photo(photo=START_PIC, caption=welcome_text, reply_markup=InlineKeyboardMarkup(buttons))
    except: await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    help_text = (
        "⦿ `/set_caption` - Use This Command To Set Your Caption\n"
        "⦿ `/see_caption` - Use This Command To See Your Caption\n"
        "⦿ `/del_caption` - Use This Command To Delete Your Caption\n\n"
        "⦿ Send A Photo To Me To Add Custom Thumbnail\n"
        "⦿ `/viewthumb` - Use This Command To See Your Thumbnail\n"
        "⦿ `/delthumb` - Use This Command To Delete Your Thumbnail\n\n"
        "⦿ `/settings` - Use This Command To Toggle Settings\n"
        "⦿ `/metadata` - Use This Command To Set Custom Metadata\n"
        "⦿ `/task` - Use This Command To Verify Your Token"
    )
    await message.reply_text(help_text)

# --- CONFIGURATION THUMBNAIL EN DIRECT ---
@bot.on_message(filters.photo & filters.private)
async def add_thumbnail_direct(client, message):
    user_id = message.from_user.id
    photo_id = message.photo.file_id
    try:
        supabase.table("bot_settings").upsert({"user_id": user_id, "thumbnail_file_id": photo_id}).execute()
        await message.reply_text("✅ **Custom Thumbnail Saved Successfully!**")
    except Exception as e:
        await message.reply_text(f"❌ **Error saving thumbnail:** {e}")

@bot.on_message(filters.command("viewthumb") & filters.private)
async def view_thumbnail(client, message):
    user_id = message.from_user.id
    try:
        res = supabase.table("bot_settings").select("thumbnail_file_id").eq("user_id", user_id).execute()
        thumb_id = res.data[0].get("thumbnail_file_id") if res.data else None
        if thumb_id:
            await message.reply_photo(photo=thumb_id, caption="🖼️ **Your Current Thumbnail**")
        else:
            await message.reply_text("❌ **You don't have any custom thumbnail set.**")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {e}")

@bot.on_message(filters.command("delthumb") & filters.private)
async def delete_thumbnail(client, message):
    user_id = message.from_user.id
    try:
        supabase.table("bot_settings").upsert({"user_id": user_id, "thumbnail_file_id": None}).execute()
        await message.reply_text("🗑️ **Custom Thumbnail Deleted Successfully.**")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {e}")

# --- SETTINGS, CAPTIONS & SUPABASE ---
@bot.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client, message):
    user_id = message.from_user.id
    try:
        res = supabase.table("bot_settings").select("random_thumb_enabled", "dump_channel_id").eq("user_id", user_id).execute()
        r_thumb = res.data[0].get("random_thumb_enabled", False) if res.data else False
        dump_id = res.data[0].get("dump_channel_id", None) if res.data else None
    except:
        r_thumb, dump_id = False, None

    status_thumb = "🟢 Enabled" if r_thumb else "🔴 Disabled"
    status_dump = f"`{dump_id}`" if dump_id else "❌ None"

    text = f"🛠 **SETTINGS PANEL**\n\n🔀 **Random Thumbnail :** {status_thumb}\n📁 **Dump Channel :** {status_dump}"
    buttons = [
        [InlineKeyboardButton("🔀 Toggle Random Thumbnail", callback_data="toggle_random_thumb")],
        [InlineKeyboardButton("📁 Set Dump Channel", callback_data="set_dump_channel")],
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_message(filters.command("set_caption") & filters.private)
async def set_caption_cmd(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        await message.reply_text("❌ **Format incorrect!** Use: `/set_caption your text {filename}`")
        return
    caption_text = message.text.split(None, 1)[1]
    try:
        supabase.table("bot_settings").upsert({"user_id": user_id, "custom_caption": caption_text}).execute()
        await message.reply_text("✅ **Caption Saved Successfully!**")
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {e}")

@bot.on_message(filters.command("see_caption") & filters.private)
async def see_caption_cmd(client, message):
    user_id = message.from_user.id
    try:
        res = supabase.table("bot_settings").select("custom_caption").eq("user_id", user_id).execute()
        current = res.data[0].get("custom_caption") if res.data else None
        if current: await message.reply_text(f"📢 **Current Caption:**\n\n`{current}`")
        else: await message.reply_text("❌ **No custom caption set.**")
    except Exception as e: await message.reply_text(f"❌ **Error:** {e}")

@bot.on_message(filters.command("del_caption") & filters.private)
async def del_caption_cmd(client, message):
    user_id = message.from_user.id
    try:
        supabase.table("bot_settings").upsert({"user_id": user_id, "custom_caption": None}).execute()
        await message.reply_text("🗑️ **Custom Caption Deleted.**")
    except Exception as e: await message.reply_text(f"❌ **Error:** {e}")

# --- RÉCEPTION ET ANALYSE DU MÉDIA ---
@bot.on_message((filters.document | filters.video) & filters.private)
async def receive_file(client, message):
    user_id = message.from_user.id
    file = message.document or message.video
    
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ File size exceeds 2GB limit.")
        return
        
    orig_ext = os.path.splitext(file.file_name)[1] if file.file_name else ".mp4"
    if not orig_ext: orig_ext = ".mp4"

    user_data[user_id] = {
        "file_id": file.file_id,
        "original_name": file.file_name,
        "orig_ext": orig_ext,
        "mime_type": file.mime_type or "video/mp4",
        "dc_id": getattr(file, "dc_id", "4")
    }
    
    info_text = (
        f"📂 **Media Info :**\n\n"
        f"♢ **File Name :** `{file.file_name}`\n"
        f"♢ **File Size :** {file.file_size / (1024*1024):.2f} MB\n"
        f"♢ **File Extension :** {orig_ext.replace('.', '')}\n"
        f"♢ **Mime Type :** {file.mime_type}\n"
        f"♢ **DC ID :** {getattr(file, 'dc_id', '4')}\n\n"
        f"**Please Enter The New Filename...**\n\n"
        f"Note:- Extension Not Required"
    )
    
    await message.reply_text(
        info_text, 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Rename", callback_data="trigger_rename"), 
             InlineKeyboardButton("⏳ Cancel", callback_data="cancel_action")]
        ])
    )

# --- INTERACTION CALLBACKS ---
@bot.on_callback_query(filters.regex("^(trigger_rename|cancel_action|toggle_random_thumb|set_dump_channel|close_settings|help_panel|about_panel|back_start)$"))
async def handle_callback_menus(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "cancel_action":
        if user_id in user_data: del user_data[user_id]
        await callback_query.message.edit("❌ **Task Cancelled Successfully.**")
    elif data == "trigger_rename":
        if user_id not in user_data:
            await callback_query.answer("❌ Session Expired.", show_alert=True)
            return
        await callback_query.message.edit("📝 **Please reply to this message with the new filename.**\n\n_Note: Extension is not required._")
        user_data[user_id]["awaiting_name"] = True
    elif data == "close_settings":
        await callback_query.message.delete()
    elif data == "toggle_random_thumb":
        try:
            res = supabase.table("bot_settings").select("random_thumb_enabled").eq("user_id", user_id).execute()
            current = res.data[0].get("random_thumb_enabled", False) if res.data else False
            supabase.table("bot_settings").upsert({"user_id": user_id, "random_thumb_enabled": not current}).execute()
            await callback_query.answer(f"Random Thumbnail : {'Disabled' if current else 'Enabled'}", show_alert=True)
            await settings_cmd(client, callback_query.message)
            await callback_query.message.delete()
        except: pass
    elif data == "set_dump_channel":
        await callback_query.message.edit("📁 **Send your Dump Channel numeric ID now.**")
        user_data[user_id] = {"awaiting_dump_id": True}
    elif data == "help_panel":
        await callback_query.message.edit_text("🛠️ **Help panel instructions loaded.** Use standard renamer rules.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]))
    elif data == "about_panel":
        await callback_query.message.edit_text("💗 **About :** 4GB Premium Renamer Core Structure.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]))
    elif data == "back_start":
        await callback_query.message.delete()
        await start_cmd(client, callback_query.message)

# --- RÉCEPTION TEXTE ---
@bot.on_message(filters.text & ~filters.command(["start", "help", "settings", "viewthumb", "delthumb", "set_caption", "see_caption", "del_caption", "metadata", "task"]) & filters.private)
async def process_text_input(client, message):
    user_id = message.from_user.id
    
    if user_id in user_data and user_data[user_id].get("awaiting_dump_id"):
        try:
            dump_id = int(message.text.strip())
            supabase.table("bot_settings").upsert({"user_id": user_id, "dump_channel_id": dump_id}).execute()
            await message.reply_text(f"✅ **Dump Channel Linked Successfully!** ID: `{dump_id}`")
        except:
            await message.reply_text("❌ Invalid ID format.")
        del user_data[user_id]
        return

    if user_id not in user_data or not user_data[user_id].get("awaiting_name"): return
    
    input_name = message.text.strip()
    orig_ext = user_data[user_id]["orig_ext"]
    
    final_name = input_name if input_name.endswith(orig_ext) else f"{input_name}{orig_ext}"
        
    user_data[user_id]["new_name"] = final_name
    user_data[user_id]["awaiting_name"] = False
    
    buttons = [[
        InlineKeyboardButton("📁 Document", callback_data=f"queue|doc"),
        InlineKeyboardButton("🎥 Video", callback_data=f"queue|video")
    ]]
    await message.reply_text(f"**Select The Output File Type**\n\n**File Name :** `{final_name}`", reply_markup=InlineKeyboardMarkup(buttons))

# --- FILES D'ATTENTE ET ENVOI ---
@bot.on_callback_query(filters.regex("^queue"))
async def add_to_queue(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data or "new_name" not in user_data[user_id]:
        await callback_query.answer("❌ Session Error.", show_alert=True)
        return

    await task_queue.put((callback_query, user_id))
    await callback_query.message.edit(f"⏳ **Added to queue...**\n📍 Global Position : `{task_queue.qsize()}`")
    asyncio.create_task(process_queue(client))

async def process_queue(client):
    global is_processing
    if is_processing: return
    is_processing = True
    
    while not task_queue.empty():
        callback_query, user_id = await task_queue.get()
        try:
            file_info = user_data.get(user_id)
            if not file_info: continue
            
            upload_type = callback_query.data.split("|")[1]
            new_name = file_info["new_name"]
            
            msg = await callback_query.message.edit(
                "🚀 ⚡ **Initialisation...** ⚡\n\n"
                "▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢▢\n\n"
                " 🔗 **Size :** 0.0 MB | -- MB"
            )
            await asyncio.sleep(1)
            
            start_time = time.time()
            custom_download_path = os.path.join(DOWNLOAD_DIR, file_info["original_name"])
            
            # Étape 1 & 2 : Téléchargement (Style 1)
            download_path = await client.download_media(
                message=file_info["file_id"], file_name=custom_download_path,
                progress=lambda c, t: progress_bar(c, t, msg, "🚀 ⚡ **Downloading Media...** ⚡", start_time, mode="download")
            )
            
            if not download_path: continue

            final_path = os.path.join(DOWNLOAD_DIR, new_name)
            os.rename(download_path, final_path)
            
            # Gestion Thumbnail
            thumb_file = None
            try:
                res = supabase.table("bot_settings").select("thumbnail_file_id", "random_thumb_enabled", "dump_channel_id", "custom_caption").eq("user_id", user_id).execute()
                settings = res.data[0] if res.data else {}
                
                if settings.get("random_thumb_enabled") and os.path.exists(DEFAULT_THUMBS_DIR):
                    files = [os.path.join(DEFAULT_THUMBS_DIR, f) for f in os.listdir(DEFAULT_THUMBS_DIR) if f.endswith(('.jpg', '.png'))]
                    if files: thumb_file = random.choice(files)
                elif settings.get("thumbnail_file_id"):
                    thumb_file = await client.download_media(message=settings["thumbnail_file_id"], file_name=os.path.join(DOWNLOAD_DIR, f"t_{user_id}.jpg"))
                
                dump_target = settings.get("dump_channel_id", user_id)
            except: dump_target = user_id

            duration, width, height = get_video_metadata(final_path)
            file_size_mo = os.path.getsize(final_path) / (1024 * 1024)
            detected_quality = f"{height}p" if height > 0 else "Original"
            duration_str = f"{duration // 60}m {duration % 60}s" if duration > 0 else "Unknown"

            custom_caption = None
            try:
                if settings.get("custom_caption"):
                    custom_caption = settings["custom_caption"].replace("{filename}", new_name).replace("{quality}", detected_quality)
            except: pass

            if not custom_caption:
                custom_caption = f"🎥 **Fichier :** `{new_name}`\n⚙️ **Qualité :** {detected_quality}\n📦 **Poids :** {file_size_mo:.1f} Mo\n⏱ **Durée :** {duration_str}"

            # Étape 3 : Envoi (Style 2)
            start_upload_time = time.time()
            target_chat = dump_target if dump_target else user_id
            
            if upload_type == "video":
                await client.send_video(
                    chat_id=target_chat, video=final_path, caption=custom_caption, thumb=thumb_file,
                    duration=duration, width=width, height=height, supports_streaming=True,
                    progress=lambda c, t: progress_bar(c, t, msg, "📤 **Envoi de la vidéo optimisée...**", start_upload_time, mode="upload")
                )
            else:
                await client.send_document(
                    chat_id=target_chat, document=final_path, caption=custom_caption, thumb=thumb_file,
                    progress=lambda c, t: progress_bar(c, t, msg, "📤 **Envoi du document optimisé...**", start_upload_time, mode="upload")
                )
            
            if target_chat != user_id:
                await client.send_message(chat_id=user_id, text=f"🚀 **File processed and sent to your Dump Channel !**\n📦 Name : `{new_name}`")

            await msg.delete()
        except Exception as e: print(f"Queue Error : {e}")
        finally:
            if 'final_path' in locals() and os.path.exists(final_path): os.remove(final_path)
            if thumb_file and os.path.exists(thumb_file) and DOWNLOAD_DIR in thumb_file: os.remove(thumb_file)
            if user_id in user_data: del user_data[user_id]
            task_queue.task_done()
    is_processing = False

if __name__ == "__main__":
    import http.server, threading
    class DummyServer(http.server.SimpleHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"Bot Running")
    def run_server(): http.server.HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), DummyServer).serve_forever()
    threading.Thread(target=run_server, daemon=True).start()
    bot.run()
