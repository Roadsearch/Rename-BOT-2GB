import os
import time
import math
import asyncio
import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client as SupabaseClient
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

# Configuration des dossiers
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Limite stricte Telegram pour les fichiers (2000 Mo)
MAX_FILE_SIZE = 2000 * 1024 * 1024 

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

def compress_video_720p(input_path, output_path):
    """Compresse un fichier géant en bridant la RAM au maximum pour Render Free."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vf='scale=-2:720',       # Downscale 4K/1080p -> 720p léger
                vcodec='libx264',        # Encodage standard
                crf=32,                  # Compression très forte pour un fichier minuscule
                preset='ultrafast',      # Zéro effort CPU, pas de mise en cache RAM
                tune='fastdecode',
                acodec='aac',
                audio_bitrate='64k',
                threads=1                # CRUCIAL : 1 seul thread pour ne pas saturer Render
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path
    except Exception as e:
        print(f"Erreur FFmpeg : {e}")
        return input_path

def get_video_metadata(file_path):
    try:
        parser = createParser(file_path)
        if parser:
            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    return (
                        int(metadata.get("duration").seconds) if metadata.has("duration") else 0,
                        int(metadata.get("width")) if metadata.has("width") else 0,
                        int(metadata.get("height")) if metadata.has("height") else 0
                    )
    except:
        pass
    return 0, 0, 0

async def progress_bar(current, total, reply_msg, text, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total: # Espacé à 5s pour économiser l'API
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        time_to_completion = round((total - current) / speed) if speed > 0 else 0
        
        progress = math.floor(percentage / 10)
        bar = "█" * progress + "░" * (10 - progress)
        
        try:
            await reply_msg.edit(
                f"{text}\n\n"
                f"|{bar}| {percentage:.2f}%\n"
                f"📦 Taille : {current / (1024*1024):.1f} / {total / (1024*1024):.1f} Mo\n"
                f"🚀 Vitesse : {speed / (1024 * 1024):.2f} Mo/s\n"
                f"⏳ Restant : {time_to_completion}s"
            )
        except:
            pass

@bot.on_message(filters.command("start") & admin_filter)
async def start_cmd(client, message):
    await message.reply_text("👋 **Bot Renamer 2Go Spécial Render Free actif.**")

@bot.on_message((filters.document | filters.video) & admin_filter)
async def receive_file(client, message):
    file = message.document or message.video
    
    # Protection contre le dépassement matériel de Telegram
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ **Erreur : Ce fichier dépasse la limite de 2 Go imposée par Telegram.**")
        return
        
    user_data[message.from_user.id] = {"file_id": file.file_id, "original_name": file.file_name}
    await message.reply_text(f"📥 **Fichier valide reçu ({file.file_size / (1024*1024):.1f} Mo).**\n\nEnvoyez le nouveau nom avec son extension.")

@bot.on_message(filters.text & ~filters.command(["start"]) & admin_filter)
async def rename_process(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    new_name = message.text.strip()
    buttons = [[
        InlineKeyboardButton("🗜️ Compresser (720p)", callback_data=f"upload_video|{new_name}"),
        InlineKeyboardButton("📁 Fichier Original", callback_data=f"upload_doc|{new_name}")
    ]]
    await message.reply_text(f"📝 Choix pour `{new_name}` :", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^upload_"))
async def start_download_upload(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data: return
        
    data = callback_query.data.split("|")
    upload_type, new_name = data[0], data[1]
    file_info = user_data[user_id]
    
    msg = await callback_query.message.edit("⚡ **Vérification de l'espace disque...**")
    start_time = time.time()
    
    # 1. Téléchargement direct vers le stockage Render
    custom_download_path = os.path.join(DOWNLOAD_DIR, file_info["original_name"])
    download_path = await client.download_media(
        message=file_info["file_id"],
        file_name=custom_download_path,
        progress=progress_bar,
        progress_args=(msg, "📥 **Téléchargement du bloc de 2 Go...**", start_time)
    )
    
    if not download_path:
        await msg.edit("❌ **Téléchargement interrompu.**")
        return

    final_path = os.path.join(DOWNLOAD_DIR, new_name)
    os.rename(download_path, final_path)

    # 2. Compression 720p si demandé (avec sécurité de nettoyage de l'original en cours de route)
    original_to_delete = None
    duration, width, height = 0, 0, 0
    if upload_type == "upload_video":
        await msg.edit("🗜️ **Compression en cours (Brido-RAM activé)...**")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"low_{new_name}")
        original_to_delete = final_path
        
        # Lancement de la tâche lourde isolée
        final_path = compress_video_720p(original_to_delete, compressed_path)
        
        # Libération immédiate de l'espace de la vidéo originale de 2 Go avant l'envoi !
        if original_to_delete and os.path.exists(original_to_delete) and final_path != original_to_delete:
            os.remove(original_to_delete)
            original_to_delete = None
            
        duration, width, height = get_video_metadata(final_path)

    # 3. Envoi sur Telegram par paquets
    await msg.edit("📤 **Initialisation du téléversement...**")
    start_time = time.time()
    
    try:
        if upload_type == "upload_video":
            await client.send_video(
                chat_id=ADMIN, video=final_path, caption=f"✅ `{new_name}`",
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(msg, "📤 **Téléversement de la vidéo compressée...**", start_time)
            )
        else:
            await client.send_document(
                chat_id=ADMIN, document=final_path, caption=f"✅ `{new_name}`",
                progress=progress_bar, progress_args=(msg, "📤 **Téléversement du fichier brut...**", start_time)
            )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Échec de l'envoi : {str(e)}")
    finally:
        # Nettoyage total
        if original_to_delete and os.path.exists(original_to_delete): os.remove(original_to_delete)
        if os.path.exists(final_path): os.remove(final_path)
        if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    print("Bot optimisé pour les fichiers lourds (2 Go) démarré !")
    bot.run()
