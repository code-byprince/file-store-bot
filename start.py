from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from config import Config
from database import db
from utils.helpers import human_size


async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    if not Config.FORCE_SUB_CHANNELS:
        return True
    for channel in Config.FORCE_SUB_CHANNELS:
        try:
            member = await context.bot.get_chat_member(f"@{channel}", user_id)
            if member.status in ("kicked", "left"):
                return False
        except Exception:
            return False
    return True


def force_sub_markup():
    buttons = [
        [InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{ch}", style="primary")]
        for ch in Config.FORCE_SUB_CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ I Joined", callback_data="check_sub", style="success")])
    return InlineKeyboardMarkup(buttons)


def main_menu_markup():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📂 My Files", callback_data="myfiles_0", style="primary"),
             InlineKeyboardButton("⭐ Favorites", callback_data="favs_0", style="success")],
            [InlineKeyboardButton("🕒 Recent Uploads", callback_data="recent_0", style="primary"),
             InlineKeyboardButton("🔎 Search", callback_data="search_hint", style="primary")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about", style="primary"),
             InlineKeyboardButton("❓ Help", callback_data="help", style="primary")],
        ]
    )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if await db.is_banned(user.id):
        await message.reply_text("🚫 You are banned from using this bot.")
        return

    await db.add_user(user.id, user.username or "", user.first_name or "")

    if not await is_subscribed(context, user.id):
        await message.reply_text(
            "🔒 Access Restricted\n\nPlease join our channel(s) below to use this bot, "
            "then tap I Joined.",
            reply_markup=force_sub_markup(),
        )
        return

    args = context.args
    if args and args[0].startswith("file_"):
        code = args[0].split("file_", 1)[1]
        await deliver_file(context, message.chat_id, code)
        return

    text = Config.WELCOME_TEXT.format(mention=user.mention_html())
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC, caption=text, reply_markup=main_menu_markup(), parse_mode="HTML"
        )
    else:
        await message.reply_text(text, reply_markup=main_menu_markup(), parse_mode="HTML")


async def deliver_file(context: ContextTypes.DEFAULT_TYPE, chat_id: int, code: str):
    file_doc = await db.get_file(code)
    if not file_doc:
        await context.bot.send_message(chat_id, "❌ File not found or the link is invalid.")
        return
    try:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=Config.DB_CHANNEL,
            message_id=file_doc["db_msg_id"],
            caption=(
                f"📄 {file_doc['file_name']}\n"
                f"💾 Size: {human_size(file_doc['file_size'])}"
            ),
        )
        await db.increment_downloads(code)
    except BadRequest as e:
        await context.bot.send_message(chat_id, f"⚠️ Could not deliver file: {e}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(HELP_TEXT)


async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(ABOUT_TEXT)


async def privacy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(PRIVACY_TEXT, disable_web_page_preview=True)


# ---------------------------------------------------------------- callbacks --
async def check_sub_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if await is_subscribed(context, query.from_user.id):
        await query.edit_message_text("✅ Thanks for joining! Send /start again.")
    else:
        await query.answer("You haven't joined all channels yet.", show_alert=True)


async def home_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = Config.WELCOME_TEXT.format(mention=query.from_user.mention_html())
    await query.edit_message_text(text, reply_markup=main_menu_markup(), parse_mode="HTML")


async def help_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        HELP_TEXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home", style="primary")]]),
    )


async def about_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        ABOUT_TEXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home", style="primary")]]),
    )


async def search_hint_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Use /search <keyword> to search your files.", show_alert=True)


HELP_TEXT = """
📖 Bot Commands

• Send me any file (photo, video, audio, PDF, ZIP, APK, anything) — I'll store it and give you a permanent link.
• /myfiles — browse your uploaded files
• /search <keyword> — search your files
• /recent — recently uploaded files
• /favorites — your starred files
• /stats — bot statistics

Tap a file in My Files to get Preview, Rename, Delete, Favorite or Share options.
"""

ABOUT_TEXT = """
ℹ️ About This Bot

🤖 Advanced File Storage Bot
⚙️ Built with python-telegram-bot + MongoDB
☁️ Hosted 24/7 on Render
🔗 Permanent, unlimited file links
"""

PRIVACY_TEXT = """
🔒 Privacy Policy

What we collect: your Telegram user ID, username, name, and the files you upload (name, size, type, upload time).

How we use it: only to run the file storage service — generating links, letting you search/rename/delete/favorite your files, and basic usage stats.

Where it's stored: files are stored in a private Telegram channel; metadata is stored in a secure MongoDB database.

Your control: you can delete any file you uploaded anytime via /myfiles. Contact the admin for full data deletion.

We never sell or share your data with third parties for advertising.
"""
