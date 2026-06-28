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

def compress_video_720p(input_path, output_path):
    """Compresse fortement une vidéo en bridant la RAM pour Render Free."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vf='scale=-2:720',       # Downscale HD 720p léger
                vcodec='libx264',        # Codec standard universel
                crf=32,                  # Compression forte (Fichier super léger)
                preset='ultrafast',      # Utilise le moins de CPU/RAM possible
                tune='fastdecode',       # Allège les calculs d'encodage
                acodec='aac',            # Audio léger
                audio_bitrate='64k',     # Flux audio minimal
                threads=1                # Bloque sur 1 seul thread pour ne pas saturer Render
            )
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path
    except Exception as e:
        print(f"Erreur FFmpeg : {e}")
        return input_path

def get_video_metadata(file_path):
    """Extrait la durée et les dimensions de la vidéo via Hachoir."""
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
    """Affiche de manière fluide la progression du transfert."""
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
    await message.reply_text("👋 **Bot Renamer Pro Spécial JishuDeveloper connecté à Supabase !**")

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
    if file.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ **Erreur : Ce fichier dépasse les 2 Go autorisés.**")
        return
    user_data[message.from_user.id] = {"file_id": file.file_id, "original_name": file.file_name}
    await message.reply_text(f"📥 **Fichier reçu :** `{file.file_name}`\n\nEnvoyez le **nouveau nom complet**.")

@bot.on_message(filters.text & ~filters.command(["start", "del_thumb"]) & admin_filter)
async def rename_process(client, message):
    user_id = message.from_user.id
    if user_id not in user_data: return
    
    new_name = message.text.strip()
    # Respect strict de la structure du callback de JishuDeveloper (3 parties séparées par |)
    buttons = [[
        InlineKeyboardButton("🎬 Vidéo (Compresser 720p)", callback_data=f"upload|video|{new_name}"),
        InlineKeyboardButton("📁 Document (Original)", callback_data=f"upload|doc|{new_name}")
    ]]
    await message.reply_text(f"📝 Choisissez le mode pour `{new_name}` :", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("^upload"))
async def start_download_upload(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in user_data: return
        
    # Découpage correct selon le modèle JishuDeveloper (3 segments séparés par |)
    data = callback_query.data.split("|")
    upload_type = data[1]  # Extrait "video" ou "doc"
    new_name = data[2]     # Extrait le nom réel du fichier texte
    
    file_info = user_data[user_id]
    msg = await callback_query.message.edit("⚡ **Initialisation...**")
    start_time = time.time()
    
    # 1. Téléchargement
    custom_download_path = os.path.join(DOWNLOAD_DIR, file_info["original_name"])
    download_path = await client.download_media(
        message=file_info["file_id"],
        file_name=custom_download_path,
        progress=progress_bar,
        progress_args=(msg, "📥 **Téléchargement depuis Telegram...**", start_time)
    )
    
    if not download_path:
        await msg.edit("❌ **Échec du téléchargement.**")
        return

    final_path = os.path.join(DOWNLOAD_DIR, new_name)
    os.rename(download_path, final_path)
    
    # 2. Récupération de la miniature
    thumb_file = None
    response = supabase.table("bot_settings").select("thumbnail_file_id").eq("user_id", ADMIN).execute()
    if response.data and len(response.data) > 0:
        thumb_id = response.data[0].get("thumbnail_file_id")
        if thumb_id:
            thumb_file_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
            thumb_file = await client.download_media(message=thumb_id, file_name=thumb_file_path)

    # 3. Traitement de la compression et Hachoir
    original_to_delete = None
    duration, width, height = 0, 0, 0
    if upload_type == "video":
        await msg.edit("🗜️ **Compression en cours (Anti-crash RAM actif)...**")
        compressed_path = os.path.join(DOWNLOAD_DIR, f"low_{new_name}")
        original_to_delete = final_path
        
        final_path = compress_video_720p(original_to_delete, compressed_path)
        
        # Destruction précoce de l'original de 2 Go pour vider l'espace disque
        if original_to_delete and os.path.exists(original_to_delete) and final_path != original_to_delete:
            os.remove(original_to_delete)
            original_to_delete = None
            
        duration, width, height = get_video_metadata(final_path)

    # 4. Envoi final
    await msg.edit("📤 **Téléversement vers Telegram...**")
    start_time = time.time()
    
    try:
        if upload_type == "video":
            await client.send_video(
                chat_id=ADMIN, video=final_path, caption=f"✅ `{new_name}`", thumb=thumb_file,
                duration=duration, width=width, height=height, supports_streaming=True,
                progress=progress_bar, progress_args=(msg, "📤 **Envoi de la vidéo allégée...**", start_time)
            )
        else:
            await client.send_document(
                chat_id=ADMIN, document=final_path, caption=f"✅ `{new_name}`", thumb=thumb_file,
                progress=progress_bar, progress_args=(msg, "📤 **Envoi du document d'origine...**", start_time)
            )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Erreur lors du téléversement : {str(e)}")
    finally:
        if original_to_delete and os.path.exists(original_to_delete): os.remove(original_to_delete)
        if os.path.exists(final_path): os.remove(final_path)
        if thumb_file and os.path.exists(thumb_file): os.remove(thumb_file)
        if user_id in user_data: del user_data[user_id]

if __name__ == "__main__":
    # 🌐 Faux serveur Web d'écoute pour satisfaire les ports imposés par Render Free
    import http.server
    import threading

    class DummyServer(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot fonctionnel !")

    def run_server():
        port = int(os.environ.get("PORT", 10000))
        server = http.server.HTTPServer(("0.0.0.0", port), DummyServer)
        server.serve_forever()

    threading.Thread(target=run_server, daemon=True).start()
print("Bot Jishu-Style optimisé 2Go démarré avec succès !")
bot.run()
