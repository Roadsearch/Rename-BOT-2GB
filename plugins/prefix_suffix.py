from pyrogram import Client, filters, enums
from helper.database import db


@Client.on_message(filters.private & filters.command('set_prefix'))
async def add_caption(client, message):

    if len(message.command) == 1:
        return await message.reply_text("**__Donnez Le Préfixe__\n\nExemple :- `/set_prefix @LabZero0`**", quote=True)
    prefix = message.text.split(" ", 1)[1]
    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    await db.set_prefix(message.from_user.id, prefix)
    await msg.edit("**Préfixe Enregistré Avec Succès ✅**")


@Client.on_message(filters.private & filters.command('del_prefix'))
async def delete_prefix(client, message):

    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    prefix = await db.get_prefix(message.from_user.id)
    if not prefix:
        return await msg.edit("**Vous N'avez Aucun Préfixe ❌**")
    await db.set_prefix(message.from_user.id, None)
    await msg.edit("**Préfixe Supprimé Avec Succès 🗑️**")


@Client.on_message(filters.private & filters.command('see_prefix'))
async def see_caption(client, message):

    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    prefix = await db.get_prefix(message.from_user.id)
    if prefix:
        await msg.edit(f"**Votre Préfixe :-**\n\n`{prefix}`")
    else:
        await msg.edit("**Vous N'avez Aucun Préfixe ❌**")


# SUFFIXE
@Client.on_message(filters.private & filters.command('set_suffix'))
async def add_csuffix(client, message):

    if len(message.command) == 1:
        return await message.reply_text("**__Donnez Le Suffixe__\n\nExemple :- `/set_suffix @LabZero0`**", quote=True)
    suffix = message.text.split(" ", 1)[1]
    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    await db.set_suffix(message.from_user.id, suffix)
    await msg.edit("**Suffixe Enregistré Avec Succès ✅**")


@Client.on_message(filters.private & filters.command('del_suffix'))
async def delete_suffix(client, message):

    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    suffix = await db.get_suffix(message.from_user.id)
    if not suffix:
        return await msg.edit("**Vous N'avez Aucun Suffixe ❌**")
    await db.set_suffix(message.from_user.id, None)
    await msg.edit("**Suffixe Supprimé Avec Succès ✅**")


@Client.on_message(filters.private & filters.command('see_suffix'))
async def see_csuffix(client, message):

    msg = await message.reply_text("Veuillez Patienter ...", quote=True)
    suffix = await db.get_suffix(message.from_user.id)
    if suffix:
        await msg.edit(f"**Votre Suffixe :-**\n\n`{suffix}`")
    else:
        await msg.edit("**Vous N'avez Aucun Suffixe ❌**")










# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
