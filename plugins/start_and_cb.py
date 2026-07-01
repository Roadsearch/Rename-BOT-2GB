
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, CallbackQuery
from helper.database import db
from config import Config, Txt  
  

@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)                
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔊 Mises à jour', url='https://t.me/LabZero0'),
        InlineKeyboardButton('♻️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Suayki')],
        [InlineKeyboardButton('❤️‍🩹 À Propos', callback_data='about'),
        InlineKeyboardButton('🛠️ Aide', callback_data='help')],
        [InlineKeyboardButton("👨‍💻 Développeur 🧑‍💻", url='https://t.me/Suayki')]
    ])
    if Config.START_PIC:
        if Config.START_PIC.lower().endswith((".gif", ".mp4")):
            await message.reply_animation(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button, quote=True)
        else:
            await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button, quote=True)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True, quote=True)
   

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data 
    if data == "start":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('🔊 Mises à jour', url='https://t.me/LabZero0'),
                InlineKeyboardButton('♻️ Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Suayki')],
                [InlineKeyboardButton('❤️‍🩹 À Propos', callback_data='about'),
                InlineKeyboardButton('🛠️ Aide', callback_data='help')],
                [InlineKeyboardButton("👨‍💻 Développeur 🧑‍💻", url='https://t.me/Suayki')]
            ])
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Canal LabZero", url="https://t.me/LabZero0")],
                [InlineKeyboardButton("🔒 Fermer", callback_data = "close"),
                InlineKeyboardButton("◀️ Retour", callback_data = "start")]
            ])            
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT.format(client.mention),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Canal LabZero", url="https://t.me/LabZero0")],
                [InlineKeyboardButton("🔒 Fermer", callback_data = "close"),
                InlineKeyboardButton("◀️ Retour", callback_data = "start")]
            ])            
        )
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
            await query.message.continue_propagation()
        except:
            await query.message.delete()
            await query.message.continue_propagation()





@Client.on_message(filters.private & filters.command(["donate", "d"]))
async def donate(client, message):
	text = Txt.DONATE_TXT
	keybord = InlineKeyboardMarkup([
        			[InlineKeyboardButton("🦋 Admin",url = "https://t.me/Suayki"), 
        			InlineKeyboardButton("✖️ Fermer",callback_data = "close") ]])
	await message.reply_text(text = text,reply_markup = keybord)



# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
