from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import db
from utils.helpers import human_size, uptime

PAGE_SIZE = 8


def file_list_markup(files, prefix: str, page: int, total: int):
    rows = []
    for f in files:
        star = "⭐" if f.get("favorite") else "▫️"
        rows.append(
            [InlineKeyboardButton(
                f"{star} {f['file_name'][:35]}", callback_data=f"open_{f['file_code']}", style="primary"
            )]
        )
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_{page-1}", style="primary"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_{page+1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home", style="success")])
    return InlineKeyboardMarkup(rows)


async def render_myfiles(user_id: int, page: int):
    total = await db.count_user_files(user_id)
    files = await db.user_files(user_id, skip=page * PAGE_SIZE, limit=PAGE_SIZE)
    if not files:
        return "📂 You haven't uploaded any files yet.", None
    text = f"📂 My Files ({total} total) — Page {page+1}"
    return text, file_list_markup(files, "myfiles", page, total)


async def render_favorites(user_id: int, page: int):
    all_favs = await db.user_favorites(user_id, skip=0, limit=10_000)
    total = len(all_favs)
    files = all_favs[page * PAGE_SIZE: page * PAGE_SIZE + PAGE_SIZE]
    if not files:
        return "⭐ You have no favorite files yet.", None
    text = f"⭐ Favorites ({total} total) — Page {page+1}"
    return text, file_list_markup(files, "favs", page, total)


async def render_recent(page: int):
    files = await db.recent_uploads(limit=PAGE_SIZE)
    if not files:
        return "🕒 No uploads yet.", None
    text = "🕒 Recent Uploads (global)"
    return text, file_list_markup(files, "recent", page, len(files))


async def myfiles_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, markup = await render_myfiles(update.effective_user.id, 0)
    await update.effective_message.reply_text(text, reply_markup=markup)


async def favorites_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, markup = await render_favorites(update.effective_user.id, 0)
    await update.effective_message.reply_text(text, reply_markup=markup)


async def recent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, markup = await render_recent(0)
    await update.effective_message.reply_text(text, reply_markup=markup)


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /search <keyword>")
        return
    keyword = " ".join(context.args)
    results = await db.search_user_files(update.effective_user.id, keyword)
    if not results:
        await update.effective_message.reply_text("🔎 No files matched your search.")
        return
    text = f"🔎 Search results for: {keyword}"
    await update.effective_message.reply_text(
        text, reply_markup=file_list_markup(results, "myfiles", 0, len(results))
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_u = await db.total_users()
    total_f = await db.total_files()
    storage = await db.total_storage_bytes()
    today = await db.today_uploads()
    online = await db.online_users()

    text = (
        "📊 Bot Dashboard\n\n"
        f"👥 Total Users: {total_u}\n"
        f"📁 Total Files: {total_f}\n"
        f"💾 Storage Used: {human_size(storage)}\n"
        f"📆 Today's Uploads: {today}\n"
        f"🟢 Online Users (10m): {online}\n"
        f"⏱ Bot Uptime: {uptime()}"
    )
    await update.effective_message.reply_text(text)


# ---------------------------------------------------------------- callbacks --
async def myfiles_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split("_")[1])
    text, markup = await render_myfiles(query.from_user.id, page)
    await query.edit_message_text(text, reply_markup=markup)


async def favs_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split("_")[1])
    text, markup = await render_favorites(query.from_user.id, page)
    await query.edit_message_text(text, reply_markup=markup)


async def recent_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split("_")[1])
    text, markup = await render_recent(page)
    await query.edit_message_text(text, reply_markup=markup)
