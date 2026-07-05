from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import Config
from database import db
from utils.helpers import human_size
from handlers.start import deliver_file

# store users waiting to type a new filename: {user_id: file_code}
PENDING_RENAME = {}


async def open_file_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("open_", 1)[1]
    f = await db.get_file(code)
    if not f:
        await query.answer("File not found.", show_alert=True)
        return
    bot_username = Config.BOT_USERNAME or (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=file_{code}"
    text = (
        f"📄 {f['file_name']}\n"
        f"💾 Size: {human_size(f['file_size'])}\n"
        f"📁 Category: {f.get('category', 'Documents')}\n"
        f"⬇️ Downloads: {f.get('downloads', 0)}\n"
        f"🔗 {link}"
    )
    is_owner = f["owner_id"] == query.from_user.id
    buttons = [[InlineKeyboardButton("⬇️ Download / Preview", callback_data=f"get_{code}", style="primary")]]
    if is_owner or query.from_user.id in Config.ADMINS:
        buttons.append(
            [
                InlineKeyboardButton(
                    "⭐ Unfavorite" if f.get("favorite") else "⭐ Favorite",
                    callback_data=f"fav_{code}",
                    style="success",
                ),
                InlineKeyboardButton("✏️ Rename", callback_data=f"ren_{code}", style="primary"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"del_{code}", style="danger"),
            ]
        )
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="myfiles_0", style="primary")])
    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True
    )


async def get_file_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("get_", 1)[1]
    await deliver_file(context, query.message.chat_id, code)
    await query.answer()


async def fav_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("fav_", 1)[1]
    new_val = await db.toggle_favorite(code)
    if new_val is None:
        await query.answer("File not found.", show_alert=True)
        return
    await query.answer("⭐ Added to favorites!" if new_val else "Removed from favorites.")


async def delete_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("del_", 1)[1]
    f = await db.get_file(code)
    if not f:
        await query.answer("File not found.", show_alert=True)
        return
    if f["owner_id"] != query.from_user.id and query.from_user.id not in Config.ADMINS:
        await query.answer("You can't delete this file.", show_alert=True)
        return
    await db.delete_file(code)
    await query.answer("🗑 File deleted.")
    await query.edit_message_text("🗑 File deleted successfully.")


async def rename_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.split("ren_", 1)[1]
    f = await db.get_file(code)
    if not f:
        await query.answer("File not found.", show_alert=True)
        return
    if f["owner_id"] != query.from_user.id and query.from_user.id not in Config.ADMINS:
        await query.answer("You can't rename this file.", show_alert=True)
        return
    PENDING_RENAME[query.from_user.id] = code
    await query.answer()
    await context.bot.send_message(query.message.chat_id, "✏️ Send me the new file name (as plain text):")


async def rename_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = PENDING_RENAME.pop(user_id, None)
    if not code:
        return
    new_name = update.effective_message.text.strip()
    await db.rename_file(code, new_name)
    await update.effective_message.reply_text(f"✅ Renamed to {new_name}")


def has_pending_rename(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id in PENDING_RENAME)
