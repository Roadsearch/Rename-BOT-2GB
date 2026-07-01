import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import Message


async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb != None:
            parser = createParser(thumb)
            metadata = extractMetadata(parser)
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
                
            # Ouvre le fichier image
            with Image.open(thumb) as img:
                # Convertit l'image en RGB et la sauvegarde dans le même fichier
                img.convert("RGB").save(thumb)
            
                # Redimensionne l'image
                resized_img = img.resize((width, height))
                
                # Sauvegarde l'image redimensionnée au format JPEG
                resized_img.save(thumb, "JPEG")
            parser.close()
    except Exception as e:
        print(e)
        thumb = None 
       
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None
    
    
async def add_metadata(input_path, output_path, metadata, ms):
    try:
        await ms.edit("<i>Métadonnées Trouvées, Ajout En Cours Dans Votre Fichier ⚡</i>")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0', '-c:s', 'copy', '-c:a', 'copy', '-c:v', 'copy',
            '-metadata', f'title={metadata}',  # Titre
            '-metadata', f'author={metadata}',  # Auteur
            '-metadata:s:s', f'title={metadata}',  # Métadonnées sous-titres
            '-metadata:s:a', f'title={metadata}',  # Métadonnées audio
            '-metadata:s:v', f'title={metadata}',  # Métadonnées vidéo
            '-metadata', f'artist={metadata}',  # Artiste
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        print(e_response)
        print(t_response)

        
        if os.path.exists(output_path):
            await ms.edit("<i>Métadonnées Ajoutées Avec Succès À Votre Fichier ✅</i>")
            return output_path
        else:
            await ms.edit("<i>Échec De L'ajout Des Métadonnées À Votre Fichier ❌</i>")
            return None
    except Exception as e:
        print(f"Une Erreur Est Survenue Lors De L'ajout Des Métadonnées : {str(e)}")
        await ms.edit("<i>Une Erreur Est Survenue Lors De L'ajout Des Métadonnées À Votre Fichier ❌</i>")
        return None






# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
