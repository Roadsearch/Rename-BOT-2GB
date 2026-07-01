from pyrogram import Client, filters, enums 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from config import Config
from helper.database import db



async def not_subscribed(_, client, message):
    await db.add_user(client, message)
    if not Config.FORCE_SUBS:
        return False
    try:             
        user = await client.get_chat_member(Config.FORCE_SUBS, message.from_user.id) 
        if user.status == enums.ChatMemberStatus.BANNED:
            return True 
        else:
            return False                
    except UserNotParticipant:
        pass
    return True


@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    buttons = [[InlineKeyboardButton(text="📢 Rejoindre Le Canal 📢", url=f"https://t.me/{Config.FORCE_SUBS}") ]]
    text = f"""<b>Bonjour {message.from_user.mention} \n\nVous Devez Rejoindre Mon Canal Pour M'utiliser\n\nMerci De Rejoindre Le Canal</b>"""
    try:
        user = await client.get_chat_member(Config.FORCE_SUBS, message.from_user.id)    
        if user.status == enums.ChatMemberStatus.BANNED:                                   
            return await client.send_message(message.from_user.id, text="Désolé, Vous Êtes Banni De L'utilisation De Ce Bot")  
    except UserNotParticipant:                       
        return await message.reply_text(text=text,quote=True, reply_markup=InlineKeyboardMarkup(buttons))
    return await message.reply_text(text=text,quote=True, reply_markup=InlineKeyboardMarkup(buttons))





# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
