import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import db
from utils.helpers import human_size


def is_admin(user_id: int) -> bool:
    return user_id in Config.ADMINS


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    text = (
        "👨‍💼 Admin Panel\n\n"
        "/broadcast <reply to a message> — send to all users\n"
        "/ban <user_id> — ban a user\n"
        "/unban <user_id> — unban a user\n"
        "/users — total users\n"
        "/searchfile <keyword> — search all files\n"
        "/dellog — view recent admin actions\n"
        "/stats — full dashboard\n"
    )
    await update.effective_message.reply_text(text)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("Reply to a message with /broadcast to send it to all users.")
        return
    user_ids = await db.all_user_ids()
    sent, failed = 0, 0
    status = await message.reply_text(f"📢 Broadcasting to {len(user_ids)} users...")
    for uid in user_ids:
        try:
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat_id,
                message_id=message.reply_to_message.message_id,
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await db.add_log(update.effective_user.id, f"Broadcast sent ({sent} ok / {failed} failed)")
    await status.edit_text(f"✅ Broadcast complete.\nSent: {sent}\nFailed: {failed}")


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /ban <user_id>")
        return
    uid = int(context.args[0])
    await db.ban_user(uid)
    await db.add_log(update.effective_user.id, f"Banned user {uid}")
    await update.effective_message.reply_text(f"🚫 User {uid} banned.")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /unban <user_id>")
        return
    uid = int(context.args[0])
    await db.unban_user(uid)
    await db.add_log(update.effective_user.id, f"Unbanned user {uid}")
    await update.effective_message.reply_text(f"✅ User {uid} unbanned.")


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    total = await db.total_users()
    await update.effective_message.reply_text(f"👥 Total Users: {total}")


async def searchfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /searchfile <keyword>")
        return
    keyword = " ".join(context.args)
    results = await db.search_all_files(keyword)
    if not results:
        await update.effective_message.reply_text("No files found.")
        return
    lines = [f"• {f['file_name']} ({human_size(f['file_size'])}) — owner {f['owner_id']}" for f in results]
    await update.effective_message.reply_text("🔎 Search Results:\n\n" + "\n".join(lines))


async def dellog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text("🚫 This command is for admins only.")
        return
    logs = await db.get_logs()
    if not logs:
        await update.effective_message.reply_text("No admin logs yet.")
        return
    lines = [f"• {l['admin_id']} — {l['action']} — {l['time'].strftime('%Y-%m-%d %H:%M')}" for l in logs]
    await update.effective_message.reply_text("📝 Admin Logs:\n\n" + "\n".join(lines))


async def get_channel_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin forwards a TEXT message FROM the private DB channel to this bot,
    and the bot replies with the exact channel ID."""
    if not is_admin(update.effective_user.id):
        return
    message = update.effective_message
    origin = message.forward_origin
    if origin and getattr(origin, "chat", None):
        fwd_chat = origin.chat
        await message.reply_text(
            f"✅ Channel Detected!\n\n"
            f"📛 Name: {fwd_chat.title}\n"
            f"🆔 ID: {fwd_chat.id}\n\n"
            f"👉 Copy this exact ID into your DB_CHANNEL environment variable on Render, then redeploy."
        )
    else:
        await message.reply_text(
            "⚠️ This doesn't look like a forward from a channel. "
            "Please forward a message directly from your private DB channel to me."
        )
