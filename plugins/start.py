"""
plugins/start.py
Commande /start — lit l'image de démarrage depuis Supabase.
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from config import Config, Txt
from helper.database import (
    add_user, is_user_exist,
    get_bot_setting,
)

logger = logging.getLogger(__name__)


async def check_force_sub(bot: Client, user_id: int) -> bool:
    if not Config.FORCE_SUBS:
        return True
    try:
        member = await bot.get_chat_member(Config.FORCE_SUBS, user_id)
        return member.status not in ("kicked", "left")
    except:
        return True


def _start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📕 Aide",     callback_data="help"),
            InlineKeyboardButton("💬 À propos", callback_data="about"),
        ],
        [
            InlineKeyboardButton("❤️ Faire un don", callback_data="donate"),
        ]
    ])


async def _send_start(bot: Client, chat_id: int, user_mention: str, edit_msg=None):
    """
    Envoie ou édite le message de démarrage.
    Lit l'image depuis Supabase (photo ou GIF).
    """
    file_id    = await get_bot_setting("start_pic_id")
    media_type = await get_bot_setting("start_pic_type") or "photo"
    text       = Txt.START_TXT.format(user_mention)
    btn        = _start_buttons()

    if edit_msg:
        # On édite un message existant (callback "Retour")
        try:
            if file_id and media_type == "photo":
                await edit_msg.edit_caption(caption=text, reply_markup=btn)
            else:
                await edit_msg.edit_text(text, reply_markup=btn)
        except:
            pass
        return

    # Nouveau message /start
    if file_id:
        if media_type == "animation":
            await bot.send_animation(
                chat_id,
                animation=file_id,
                caption=text,
                reply_markup=btn,
            )
        else:
            await bot.send_photo(
                chat_id,
                photo=file_id,
                caption=text,
                reply_markup=btn,
            )
    else:
        await bot.send_message(chat_id, text, reply_markup=btn)


# ── /start ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("start"))
async def start_cmd(bot: Client, msg: Message):
    user = msg.from_user

    # Force subscribe
    if not await check_force_sub(bot, user.id):
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📢 Rejoindre le canal",
                url=f"https://t.me/{Config.FORCE_SUBS}"
            ),
            InlineKeyboardButton("✅ J'ai rejoint", callback_data="check_sub"),
        ]])
        await msg.reply_text(
            "**Tu dois rejoindre notre canal avant d'utiliser ce bot !**",
            reply_markup=btn,
        )
        return

    # Enregistrement Supabase
    if not await is_user_exist(user.id):
        await add_user(user.id)
        if Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"**#NouvelUtilisateur**\n\n"
                    f"**Nom :** {user.mention}\n"
                    f"**ID :** `{user.id}`\n"
                    f"**Username :** @{user.username}",
                )
            except:
                pass
        logger.info(f"[Start] Nouvel utilisateur : {user.id}")

    await _send_start(bot, msg.chat.id, user.mention)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("check_sub"))
async def check_sub_cb(bot: Client, cb: CallbackQuery):
    if await check_force_sub(bot, cb.from_user.id):
        await cb.message.delete()
        await _send_start(bot, cb.message.chat.id, cb.from_user.mention)
    else:
        await cb.answer("❌ Tu n'as pas encore rejoint le canal !", show_alert=True)


@Client.on_callback_query(filters.regex("^help$"))
async def help_cb(bot: Client, cb: CallbackQuery):
    await cb.message.edit_text(
        Txt.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour", callback_data="start"),
        ]])
    )


@Client.on_callback_query(filters.regex("^about$"))
async def about_cb(bot: Client, cb: CallbackQuery):
    await cb.message.edit_text(
        Txt.ABOUT_TXT.format(cb.from_user.mention),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour", callback_data="start"),
        ]])
    )


@Client.on_callback_query(filters.regex("^donate$"))
async def donate_cb(bot: Client, cb: CallbackQuery):
    await cb.message.edit_text(
        Txt.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Retour", callback_data="start"),
        ]])
    )


@Client.on_callback_query(filters.regex("^start$"))
async def back_to_start(bot: Client, cb: CallbackQuery):
    await _send_start(bot, cb.message.chat.id, cb.from_user.mention, edit_msg=cb.message)
