"""
plugins/mystats.py
Fonctionnalité 8 — /mystats : statistiques personnelles de l'utilisateur.
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import (
    get_files_count, get_thumbnail, get_caption,
    get_prefix, get_suffix, get_metadata, get_auto_delete,
    get_rename_rule,
)

logger = logging.getLogger(__name__)


@Client.on_message(filters.private & filters.command("mystats"))
async def mystats_cmd(bot: Client, msg: Message):
    user    = msg.from_user
    user_id = user.id

    files_count = await get_files_count(user_id)
    thumbnail   = await get_thumbnail(user_id)
    caption     = await get_caption(user_id)
    prefix      = await get_prefix(user_id)
    suffix      = await get_suffix(user_id)
    metadata    = await get_metadata(user_id)
    rename_rule = await get_rename_rule(user_id)
    auto_del    = await get_auto_delete(user_id)

    def fmt(val, max_len=30):
        if not val:
            return "❌ Non défini"
        return f"`{val[:max_len]}{'…' if len(val) > max_len else ''}`"

    auto_del_txt = (
        f"`{auto_del // 60} min {auto_del % 60} s`"
        if auto_del >= 60
        else f"`{auto_del} secondes`"
    )

    text = (
        f"📊 **Tes statistiques**\n"
        f"{'─' * 28}\n\n"
        f"👤 **Nom :** {user.mention}\n"
        f"🆔 **ID :** `{user_id}`\n\n"
        f"📁 **Fichiers traités :** `{files_count}`\n\n"
        f"{'─' * 28}\n"
        f"⚙️ **Préférences actuelles**\n\n"
        f"🖼️ **Miniature :** {'✅ Définie' if thumbnail else '❌ Non définie'}\n"
        f"📝 **Légende :** {fmt(caption)}\n"
        f"🔤 **Préfixe :** {fmt(prefix)}\n"
        f"🔤 **Suffixe :** {fmt(suffix)}\n"
        f"🏷️ **Métadonnées :** {fmt(metadata)}\n"
        f"🔁 **Règle regex :** {fmt(rename_rule)}\n"
        f"⏱️ **Auto-suppression :** {auto_del_txt}\n"
    )

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖼️ Voir miniature", callback_data="stats_thumb"),
            InlineKeyboardButton("🔄 Réinitialiser tout", callback_data="stats_reset"),
        ]
    ])

    await msg.reply_text(text, reply_markup=btn)


@Client.on_callback_query(filters.regex("^stats_thumb$"))
async def stats_thumb_cb(bot: Client, cb):
    thumb = await get_thumbnail(cb.from_user.id)
    if not thumb:
        await cb.answer("❌ Aucune miniature définie.", show_alert=True)
        return
    await cb.message.reply_photo(photo=thumb, caption="🖼️ **Ta miniature actuelle**")
    await cb.answer()


@Client.on_callback_query(filters.regex("^stats_reset$"))
async def stats_reset_cb(bot: Client, cb):
    """Demande confirmation avant de tout réinitialiser."""
    await cb.message.edit_text(
        "⚠️ **Réinitialisation complète**\n\n"
        "Cela supprimera :\n"
        "• Miniature\n• Légende\n• Préfixe\n• Suffixe\n"
        "• Métadonnées\n• Règle regex\n\n"
        "**Confirmer ?**",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Oui, tout supprimer", callback_data="stats_reset_confirm"),
                InlineKeyboardButton("❌ Annuler", callback_data="stats_reset_cancel"),
            ]
        ])
    )


@Client.on_callback_query(filters.regex("^stats_reset_confirm$"))
async def stats_reset_confirm_cb(bot: Client, cb):
    from helper.database import (
        del_thumbnail, del_caption, del_prefix,
        del_suffix, del_metadata, del_rename_rule,
    )
    user_id = cb.from_user.id
    await del_thumbnail(user_id)
    await del_caption(user_id)
    await del_prefix(user_id)
    await del_suffix(user_id)
    await del_metadata(user_id)
    await del_rename_rule(user_id)
    await cb.message.edit_text("✅ **Toutes tes préférences ont été réinitialisées.**")
    logger.info(f"[Stats] Reset complet pour {user_id}")


@Client.on_callback_query(filters.regex("^stats_reset_cancel$"))
async def stats_reset_cancel_cb(bot: Client, cb):
    await cb.message.delete()
    await cb.answer("Annulé.")
