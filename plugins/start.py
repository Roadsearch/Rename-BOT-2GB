from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import Config, Txt
from helper.database import add_user, is_user_exist


async def check_force_sub(bot: Client, user_id: int) -> bool:
    """Retourne True si l'utilisateur est bien abonné au canal force-sub."""
    if not Config.FORCE_SUBS:
        return True
    try:
        member = await bot.get_chat_member(Config.FORCE_SUBS, user_id)
        return member.status not in ("kicked", "left")
    except:
        return True


@Client.on_message(filters.private & filters.command("start"))
async def start_cmd(bot: Client, msg: Message):
    user = msg.from_user

    # Force subscribe
    if not await check_force_sub(bot, user.id):
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{Config.FORCE_SUBS}"),
            InlineKeyboardButton("✅ I Joined", callback_data="check_sub")
        ]])
        await msg.reply_text(
            "**You Need To Join Our Channel First To Use This Bot!**",
            reply_markup=btn
        )
        return

    # Enregistrement Supabase
    if not await is_user_exist(user.id):
        await add_user(user.id)
        if Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"**#NewUser**\n\n"
                    f"**Name :** {user.mention}\n"
                    f"**ID :** `{user.id}`\n"
                    f"**Username :** @{user.username}"
                )
            except:
                pass

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📕 Help", callback_data="help"),
            InlineKeyboardButton("💬 About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("❤️ Donate", callback_data="donate"),
        ]
    ])

    if Config.START_PIC:
        await msg.reply_photo(
            photo=Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=btn
        )
    else:
        await msg.reply_text(
            Txt.START_TXT.format(user.mention),
            reply_markup=btn
        )


@Client.on_callback_query(filters.regex("check_sub"))
async def check_sub_cb(bot: Client, cb):
    if await check_force_sub(bot, cb.from_user.id):
        await cb.message.delete()
        await start_cmd(bot, cb.message)
    else:
        await cb.answer("❌ You haven't joined yet!", show_alert=True)


@Client.on_callback_query(filters.regex("help"))
async def help_cb(bot: Client, cb):
    await cb.message.edit_text(
        Txt.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]])
    )


@Client.on_callback_query(filters.regex("about"))
async def about_cb(bot: Client, cb):
    await cb.message.edit_text(
        Txt.ABOUT_TXT.format(cb.from_user.mention),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]])
    )


@Client.on_callback_query(filters.regex("donate"))
async def donate_cb(bot: Client, cb):
    await cb.message.edit_text(
        Txt.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]])
    )


@Client.on_callback_query(filters.regex("^start$"))
async def back_to_start(bot: Client, cb):
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📕 Help", callback_data="help"),
            InlineKeyboardButton("💬 About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("❤️ Donate", callback_data="donate"),
        ]
    ])
    if Config.START_PIC:
        await cb.message.edit_caption(
            caption=Txt.START_TXT.format(cb.from_user.mention),
            reply_markup=btn
        )
    else:
        await cb.message.edit_text(
            Txt.START_TXT.format(cb.from_user.mention),
            reply_markup=btn
        )
