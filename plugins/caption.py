from pyrogram import Client, filters 
from helper.database import db

@Client.on_message(filters.private & filters.command(['set_caption', "sc"]))
async def add_caption(client, message):
    if len(message.command) == 1:
       return await message.reply_text("**Donnez La Légende\n\nExemple :- `/set_caption 📕Nom ➠ : {filename} \n\n🔗 Taille ➠ : {filesize} \n\n⏰ Durée ➠ : {duration}`**", quote=True)
    caption = message.text.split(" ", 1)[1]
    await db.set_caption(message.from_user.id, caption=caption)
    await message.reply_text("**Votre Légende A Bien Été Ajoutée ✅**", quote=True)
   
@Client.on_message(filters.private & filters.command(['del_caption', "dc"]))
async def delete_caption(client, message):
    caption = await db.get_caption(message.from_user.id)  
    if not caption:
       return await message.reply_text("**Vous N'avez Aucune Légende ❌**", quote=True)
    await db.set_caption(message.from_user.id, caption=None)
    await message.reply_text("**Votre Légende A Bien Été Supprimée 🗑️**", quote=True)
                                       
@Client.on_message(filters.private & filters.command(['see_caption', 'view_caption', "vc"]))
async def see_caption(client, message):
    caption = await db.get_caption(message.from_user.id)  
    if caption:
       await message.reply_text(f"**Votre Légende :**\n\n`{caption}`", quote=True)
    else:
       await message.reply_text("**Vous N'avez Aucune Légende ❌**", quote=True)









# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
