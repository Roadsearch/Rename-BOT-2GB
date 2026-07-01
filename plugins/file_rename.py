from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from helper.ffmpeg import fix_thumb, take_screen_shot, add_metadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import db
from asyncio import sleep
from PIL import Image
import os, time, re, random, asyncio


@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name  
    if file.file_size > 2000 * 1024 * 1024:
         return await message.reply_text("Désolé, Ce Bot Ne Prend Pas En Charge Les Fichiers De Plus De 2GB", quote=True)

    try:
        await message.reply_text(
            text=f"**Veuillez Entrer Le Nouveau Nom De Fichier...**\n\n**Ancien Nom De Fichier** :- `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Veuillez Entrer Le Nouveau Nom De Fichier**\n\n**Ancien Nom De Fichier** :- `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )
    except:
        pass



@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = [[InlineKeyboardButton("📁 Document",callback_data = "upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Vidéo", callback_data = "upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data = "upload_audio")])
        await message.reply(
            text=f"**Sélectionnez Le Type De Fichier De Sortie**\n\n**Nom Du Fichier :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )



@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):    
    # Création du dossier pour les métadonnées
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
        
    # Récupération des informations nécessaires    
    prefix = await db.get_prefix(update.message.chat.id)
    suffix = await db.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Un Problème Est Survenu, Impossible De Définir Le Préfixe Ou Le Suffixe 🥺 \n\n**Contactez Mon Créateur :** @Suayki\n\n**Erreur :** `{e}`")
    
    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("🚀 Tentative De Téléchargement...  ⚡")    
    try:
     	path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram,progress_args=("🚀 Téléchargement En Cours...  ⚡", ms, time.time()))                    
    except Exception as e:
     	return await ms.edit(e)
    

    # Ajout des métadonnées
    _bool_metadata = await db.get_metadata(update.message.chat.id) 
    
    if _bool_metadata:
        metadata = await db.get_metadata_code(update.message.chat.id)
        metadata_path = f"Metadata/{new_filename}"
        await add_metadata(path, metadata_path, metadata, ms)
    else:
        await ms.edit("⏳ Changement De Mode...  ⚡")

    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata.has("duration"):
           duration = metadata.get('duration').seconds
        parser.close()   
    except:
        pass
        
    ph_path = None
    user_id = int(update.message.chat.id) 
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
         try:
             caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
         except Exception as e:
             return await ms.edit(text=f"Erreur Dans Votre Légende, Argument Non Reconnu : ({e})")             
    else:
         caption = f"**{new_filename}**"
 
    if (media.thumbs or c_thumb):
         if c_thumb:
             ph_path = await bot.download_media(c_thumb)
             width, height, ph_path = await fix_thumb(ph_path)
         else:
             try:
                 ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, duration - 1))
                 width, height, ph_path = await fix_thumb(ph_path_)
             except Exception as e:
                 ph_path = None
                 print(e)  


    await ms.edit("💠 Tentative D'envoi...  ⚡")
    type = update.data.split("_")[1]
    try:
        if type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=metadata_path if _bool_metadata else file_path,
                thumb=ph_path, 
                caption=caption, 
                progress=progress_for_pyrogram,
                progress_args=("💠 Envoi En Cours...  ⚡", ms, time.time()))

        elif type == "video": 
            await bot.send_video(
                update.message.chat.id,
                video=metadata_path if _bool_metadata else file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Envoi En Cours...  ⚡", ms, time.time()))

        elif type == "audio": 
            await bot.send_audio(
                update.message.chat.id,
                audio=metadata_path if _bool_metadata else file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Envoi En Cours...  ⚡", ms, time.time()))


    except Exception as e:          
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        return await ms.edit(f"**Erreur :** `{e}`")    
 
    await ms.delete() 
    if ph_path:
        os.remove(ph_path)
    if file_path:
        os.remove(file_path)




# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
