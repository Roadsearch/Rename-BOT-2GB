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

def get_target_resolution(current_height):
    """Détermine le palier de qualité inférieur selon les normes standards."""
    if current_height >= 2160:     # 4K -> 1080p
        return 1920, 1080, "1080p (Full HD)"
    elif current_height >= 1080:   # Full HD -> 720p
        return 1280, 720, "720p (HD)"
    elif current_height >= 720:    # HD -> 480p
        return 854, 480, "480p (SD)"
    elif current_height >= 480:    # 480p -> 360p
        return 640, 360, "360p"
    elif current_height >= 360:    # 360p -> 240p
        return 426, 240, "240p"
    else:                          # 240p -> 144p
        return 256, 144, "144p"

def compress_video_adaptive(input_path, output_path, current_height):
    """Compresse la vidéo vers le format inférieur en bloquant la RAM sur Render."""
    target_width, target_height, label = get_target_resolution(current_height)
    try:
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vf=f'scale={target_width}:{target_height}', 
                vcodec='libx264',        # Requis pour le streaming direct
                pix_fmt='yuv420p',       # Résout l'erreur "Impossible de lire la vidéo"
                crf=28,                  # Équilibre parfait poids/visuel
                preset='ultrafast',      # Sauvegarde la RAM de Render Free
                tune='fastdecode',
                acodec='aac',            # Format audio universel
                audio_bitrate='64k',
                threads=1                # Fixé sur 1 seul cœur CPU
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path, label
    except Exception as e:
        print(f"Erreur FFmpeg : {e}")
        return input_path, "Original"

def get_video_metadata(file_path):
    """Extrait proprement la durée et les dimensions via Hachoir."""
    duration, width, height = 0, 0, 0
    try:
        parser = createParser(file_path)
        if parser:
            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    if metadata.has("duration"):
                        duration = int(metadata.get("duration").seconds)
                    if metadata.has("width"):
                        width = int(metadata.get("width"))
                    if metadata.has("height"):
                        height = int(metadata.get("height"))
    except:
        pass
    return duration, width, height

async def progress_bar(current, total, reply_msg, text, start_time):
    """Affiche la barre de progression sans division par zéro."""
    if not total or total == 0: return
    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total:
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
    await message.reply_text("👋 **Bot Renamer Adaptatif 2Go connecté à Supabase !**")

@bot.on_message(filters.photo & admin_filter)
async def save_thumbnail(client, message):
    msg = await message.reply_text("📥 *Sauvegarde de la miniature...*")
    supabase.table("bot_settings").upsert({"user_id": ADMIN, "thumbnail_file_id": message.photo.file_id}).execute()
    await msg.edit("✅ **Miniature synchronisée de manière permanente !**")

@bot.on_message((filters.document | filters.video) & admin_filter)
async def receive_file(client, message):
    file = message.document or message.video
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ **Erreur : Ce fichier dépasse la limite de 2 Go.**")
        return
    user_data[message.from_user.id] = {"file_id": file.file_id, "original_name": file.file_name}
    await message.reply_text(f"📥 **Fichier reçu :** `{file.file_name}`\n\nEnvoyez le **nouveau nom complet**.")

@bot.on_message(filters.text & ~filters.command(["start"]) & admin_filter)
async def rename_process(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    new_name = message.text.strip()
    buttons = [[
        InlineKeyboardButton("🎬 Vidéo (Auto-Compression)", callback_data=f"upload|video|{new_name}"),
        InlineKeyboardButton("📁 Document (Fichier Brut)", callback_data=f"upload|doc|{new_name}")
    ]]
    await message.reply_text(f"📝 Choisissez le format pour `{new_name}` :", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^upload"))
async def start_download_upload(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data: return
        
    data = callback_query.data.split("|")
    upload_type = data[1]
    new_name = data[2]
    
    file_info = user_data[user_id]
    msg = await callback_query.message.edit("⚡ **Initialisation...**")
    start_time = time.time()
    
    # 1. Téléchargement
    custom_download_path = os.path.join(DOWNLOAD_DIR, file_info["original_name"])
    download_path = await client.download_media(
        message=file_info["file_id"], file_name=custom_download_path,
        progress=progress_bar, progress_args=(msg, "📥 **Téléchargement depuis Telegram...**", start_time)
    )
    
    if not download_path:
        await msg.edit("❌ **Téléchargement échoué.**")
        return

    final_path = os.path.join(DOWNLOAD_DIR, new_name)
    os.rename(download_path, final_path)
    
    # 2. Récupération de la miniature Supabase (Sécurisée)
    thumb_file = None
    try:
        response = supabase.table("bot_settings").select("thumbnail_file_id").eq("user_id", ADMIN).execute()
        if response and response.data and len(response.data) > 0:
            thumb_id = response.data[0].get("thumbnail_file_id")
            if thumb_id:
                thumb_file_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
                thumb_file = await client.download_media(message=thumb_id, file_name=thumb_file_path)
    except Exception as e:
        print(f"Erreur lors de la récupération de la miniature : {e}")

    # 3. Encodage adaptatif de la vidéo
    original_to_delete = None
    duration, width, height = 0, 0, 0
    target_label = "Fichier Brut"
    
    if upload_type == "video":
        await msg.edit("⚙️ **Analyse des dimensions d'origine (Hachoir)...**")
        _, _, orig_height = get_video_metadata(final_path)
        if orig_height == 0: orig_height = 1080
            
        await msg.edit("🗜️ **Optimisation de la qualité en cours...**")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"low_{new_name}")
        original_to_delete = final_path
        
        final_path, target_label = compress_video_adaptive(original_to_delete, compressed_path, orig_height)
        
        # Nettoyage immédiat du gros fichier d'origine pour libérer le disque de Render
        if original_to_delete and os.path.exists(original_to_delete) and final_path != original_to_delete:
            os.remove(original_to_delete)
            original_to_delete = None
            
        duration, width, height = get_video_metadata(final_path)

    # 4. Envoi final avec légende (caption) enrichie
    await msg.edit("📤 **Téléversement vers Telegram...**")
    start_time = time.time()
    
    file_size_mo = os.path.getsize(final_path) / (1024 * 1024)
    
    caption_text = (
        f"🎥 **Fichier :** `{new_name}`\n"
        f"⚙️ **Qualité :** `{target_label}`\n"
        f"📦 **Poids :** `{file_size_mo:.1f} Mo`\n"
    )
    if duration > 0:
        minutes = duration // 60
        secondes = duration % 60
        caption_text += f"⏱️ **Durée :** `{minutes}m {secondes}s`"

    try:
        if upload_type == "video":
            await client.send_video(
                chat_id=ADMIN, video=final_path, caption=caption_text, thumb=thumb_file,
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(msg, "📤 **Envoi de la vidéo optimisée...**", start_time)
            )
        else:
            await client.send_document(
                chat_id=ADMIN, document=final_path, caption=caption_text, thumb=thumb_file,
                progress=progress_bar, progress_args=(msg, "📤 Envoi du document d'origine...", start_time)
            )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Échec de l'envoi : {str(e)}")
    finally:
        if original_to_delete and os.path.exists(original_to_delete): os.remove(original_to_delete)
        if os.path.exists(final_path): os.remove(final_path)
        if thumb_file and os.path.exists(thumb_file): os.remove(thumb_file)
        if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    # Serveur HTTP virtuel pour maintenir Render Free actif
    import http.server
    import threading

    class DummyServer(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot actif")

    def run_server():
        port = int(os.environ.get("PORT", 10000))
        http.server.HTTPServer(("0.0.0.0", port), DummyServer).serve_forever()

    threading.Thread(target=run_server, daemon=True).start()
    print("Bot Jishu-Style Pro 2Go prêt !")
    bot.run()
