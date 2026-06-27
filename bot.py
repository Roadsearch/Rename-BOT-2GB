import os
import time
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client as SupabaseClient

# Chargement des variables d'environnement (Render)
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN = int(os.environ.get("ADMIN", 0))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

bot = Client("AdvancedRenamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

user_data = {}
admin_filter = filters.user(ADMIN)

# Fonction d'affichage de la barre de progression (Amélioration majeure)
async def progress_bar(current, total, reply_msg, text, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total: # Mise à jour toutes les 4 secondes
        percentage = current * 100 / total
        speed = current / diff
        time_to_completion = round((total - current) / speed)
        
        # Formatage visuel [██░░░░░░░░]
        progress = math.floor(percentage / 10)
        bar = "█" * progress + "░" * (10 - progress)
        
        try:
            await reply_msg.edit(
                f"{text}\n\n"
                f"|{bar}| {percentage:.2f}%\n"
                f"🚀 Vitesse : {speed / (1024 * 1024):.2f} Mo/s\n"
                f"⏳ Restant : {time_to_completion}s"
            )
        except:
            pass

@bot.on_message(filters.command("start") & admin_filter)
async def start_cmd(client, message):
    await message.reply_text("👋 **Bot Renamer Pro connecté à Supabase !**\n\nEnvoyez-moi un média pour commencer.")

@bot.on_message(filters.photo & admin_filter)
async def save_thumbnail(client, message):
    msg = await message.reply_text("📥 *Sauvegarde de la miniature dans Supabase...*")
    supabase.table("bot_settings").upsert({"user_id": ADMIN, "thumbnail_file_id": message.photo.file_id}).execute()
    await msg.edit("✅ **Miniature synchronisée de manière permanente !**")

@bot.on_message(filters.command("del_thumb") & admin_filter)
async def delete_thumbnail(client, message):
    supabase.table("bot_settings").delete().eq("user_id", ADMIN).execute()
    await message.reply_text("🗑️ **Miniature supprimée.**")

@bot.on_message((filters.document | filters.video) & admin_filter)
async def receive_file(client, message):
    file = message.document or message.video
    user_data[message.from_user.id] = {"file_id": file.file_id, "original_name": file.file_name}
    await message.reply_text(f"📥 **Fichier reçu :** `{file.file_name}`\n\nRépondez avec le **nouveau nom complet** (ex: `Video.mp4`).")

@bot.on_message(filters.text & ~filters.command(["start", "del_thumb"]) & admin_filter)
async def rename_process(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    new_name = message.text.strip()
    buttons = [[
        InlineKeyboardButton("🎬 Vidéo MP4", callback_data=f"upload_video|{new_name}"),
        InlineKeyboardButton("📁 Fichier Brut", callback_data=f"upload_doc|{new_name}")
    ]]
    await message.reply_text(f"📝 Nouveau nom : `{new_name}`", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^upload_"))
async def start_download_upload(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data: return
        
    data = callback_query.data.split("|")
    upload_type, new_name = data[0], data[1]
    file_info = user_data[user_id]
    
    msg = await callback_query.message.edit("⚡ **Initialisation...**")
    start_time = time.time()
    
    # 1. Téléchargement avec barre de progression
    download_path = await client.download_media(
        message=file_info["file_id"],
        progress=progress_bar,
        progress_args=(msg, "📥 **Téléchargement depuis Telegram...**", start_time)
    )
    
    directory = os.path.dirname(download_path)
    final_path = os.path.join(directory, new_name)
    os.rename(download_path, final_path)
    
    # 2. Gestion de la miniature
    thumb_file = None
    response = supabase.table("bot_settings").select("thumbnail_file_id").eq("user_id", ADMIN).execute()
    if response.data:
        thumb_file = await client.download_media(message=response.data[0]["thumbnail_file_id"], file_name="thumb.jpg")

    # 3. Téléversement avec barre de progression
    await msg.edit("⚡ **Préparation du téléversement...**")
    start_time = time.time()
    
    try:
        if upload_type == "upload_video":
            await client.send_video(
                chat_id=ADMIN, video=final_path, caption=f"✅ `{new_name}`", thumb=thumb_file,
                progress=progress_bar, progress_args=(msg, "📤 **Envoi de la vidéo sur Telegram...**", start_time)
            )
        else:
            await client.send_document(
                chat_id=ADMIN, document=final_path, caption=f"✅ `{new_name}`", thumb=thumb_file,
                progress=progress_bar, progress_args=(msg, "📤 **Envoi du fichier sur Telegram...**", start_time)
            )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Erreur : {str(e)}")
    finally:
        if os.path.exists(final_path): os.remove(final_path)
        if thumb_file and os.path.exists(thumb_file): os.remove(thumb_file)
        del user_data[user_id]

if __name__ == "__main__":
    bot.run()
