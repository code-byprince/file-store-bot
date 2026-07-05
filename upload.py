import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import Config
from database import db
from utils.helpers import encode_code, human_size, detect_category
from handlers.start import is_subscribed, force_sub_markup


def extract_file_info(message):
    if message.document:
        d = message.document
        return "document", d.file_name or "document", d.file_size
    if message.video:
        v = message.video
        return "video", v.file_name or "video.mp4", v.file_size
    if message.audio:
        a = message.audio
        return "audio", a.file_name or "audio.mp3", a.file_size
    if message.voice:
        v = message.voice
        return "voice", "voice_message.ogg", v.file_size
    if message.photo:
        p = message.photo[-1]
        return "photo", "photo.jpg", p.file_size
    return None, None, None


async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if await db.is_banned(user.id):
        await message.reply_text("🚫 You are banned from using this bot.")
        return

    if not await is_subscribed(context, user.id):
        await message.reply_text("🔒 Please join our channel(s) first.", reply_markup=force_sub_markup())
        return

    file_type, file_name, file_size = extract_file_info(message)
    if not file_type:
        return

    status = await message.reply_text("⏳ Uploading & generating permanent link...")

    try:
        copied = await context.bot.copy_message(
            chat_id=Config.DB_CHANNEL,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )
    except Exception as e:
        await status.edit_text(f"❌ Upload failed: {e}")
        return

    code = encode_code(copied.message_id)
    category = detect_category(file_type, file_name)

    await db.save_file(
        {
            "file_code": code,
            "db_msg_id": copied.message_id,
            "owner_id": user.id,
            "file_name": file_name,
            "file_size": file_size or 0,
            "file_type": file_type,
            "category": category,
            "favorite": False,
            "downloads": 0,
            "uploaded_at": datetime.datetime.utcnow(),
        }
    )

    bot_username = Config.BOT_USERNAME or (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=file_{code}"

    caption = (
        f"✅ File Stored Successfully!\n\n"
        f"📄 Name: {file_name}\n"
        f"💾 Size: {human_size(file_size or 0)}\n"
        f"📁 Category: {category}\n\n"
        f"🔗 Permanent Link:\n{link}"
    )

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔗 Share Link", switch_inline_query=link, style="primary")],
            [
                InlineKeyboardButton("⭐ Favorite", callback_data=f"fav_{code}", style="success"),
                InlineKeyboardButton("✏️ Rename", callback_data=f"ren_{code}", style="primary"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"del_{code}", style="danger"),
            ],
        ]
    )
    await status.edit_text(caption, reply_markup=markup, disable_web_page_preview=True)
