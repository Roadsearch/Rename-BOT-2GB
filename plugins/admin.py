"""
plugins/admin.py
Commandes réservées aux admins : broadcast, status, restart.
"""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helper.database import get_all_users, total_users_count

admin_filter = filters.user(Config.ADMIN)


@Client.on_message(filters.private & admin_filter & filters.command("broadcast"))
async def broadcast_cmd(bot: Client, msg: Message):
    if not msg.reply_to_message:
        await msg.reply_text("**Reply to a message to broadcast it.**")
        return

    users  = await get_all_users()
    total  = len(users)
    done   = 0
    failed = 0

    status = await msg.reply_text(f"📡 **Broadcasting to {total} users...**")

    for uid in users:
        try:
            await msg.reply_to_message.copy(uid)
            done += 1
        except:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"✅ **Broadcast done!**\n\n"
        f"👥 Total  : `{total}`\n"
        f"✔️ Sent   : `{done}`\n"
        f"❌ Failed : `{failed}`"
    )


@Client.on_message(filters.private & admin_filter & filters.command("status"))
async def status_cmd(bot: Client, msg: Message):
    count = await total_users_count()
    await msg.reply_text(
        f"📊 **Bot Status**\n\n"
        f"👥 Total users : `{count}`"
    )


@Client.on_message(filters.private & admin_filter & filters.command("restart"))
async def restart_cmd(bot: Client, msg: Message):
    await msg.reply_text("♻️ **Restarting...**")
    import os, sys
    os.execv(sys.executable, [sys.executable] + sys.argv)
