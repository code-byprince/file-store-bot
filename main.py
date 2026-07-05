import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import Config
from keep_alive import keep_alive

from handlers import start as start_h
from handlers import upload as upload_h
from handlers import myfiles as myfiles_h
from handlers import callbacks as callbacks_h
from handlers import admin as admin_h

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def text_router(update: Update, context):
    """Routes plain text messages: rename flow first, then admin channel-id detection."""
    user_id = update.effective_user.id if update.effective_user else None

    # 1. If this admin/user has a pending rename, handle that first.
    if user_id in callbacks_h.PENDING_RENAME:
        await callbacks_h.rename_text_handler(update, context)
        return

    # 2. If it's a forwarded message (e.g. admin forwarding from DB channel), try channel-id detection.
    if update.effective_message.forward_origin:
        await admin_h.get_channel_id_handler(update, context)
        return


def build_application() -> Application:
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # ---- Commands ----
    application.add_handler(CommandHandler("start", start_h.start_cmd))
    application.add_handler(CommandHandler("help", start_h.help_cmd))
    application.add_handler(CommandHandler("about", start_h.about_cmd))
    application.add_handler(CommandHandler("privacy", start_h.privacy_cmd))

    application.add_handler(CommandHandler("myfiles", myfiles_h.myfiles_cmd))
    application.add_handler(CommandHandler("favorites", myfiles_h.favorites_cmd))
    application.add_handler(CommandHandler("recent", myfiles_h.recent_cmd))
    application.add_handler(CommandHandler("search", myfiles_h.search_cmd))
    application.add_handler(CommandHandler("stats", myfiles_h.stats_cmd))

    application.add_handler(CommandHandler("admin", admin_h.admin_panel))
    application.add_handler(CommandHandler("broadcast", admin_h.broadcast_cmd))
    application.add_handler(CommandHandler("ban", admin_h.ban_cmd))
    application.add_handler(CommandHandler("unban", admin_h.unban_cmd))
    application.add_handler(CommandHandler("users", admin_h.users_cmd))
    application.add_handler(CommandHandler("searchfile", admin_h.searchfile_cmd))
    application.add_handler(CommandHandler("dellog", admin_h.dellog_cmd))

    # ---- File uploads ----
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & (filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.VOICE | filters.PHOTO),
            upload_h.handle_upload,
        )
    )

    # ---- Plain text router (rename flow + channel-id detection) ----
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, text_router)
    )

    # ---- Callback queries (inline buttons) ----
    application.add_handler(CallbackQueryHandler(start_h.check_sub_cb, pattern=r"^check_sub$"))
    application.add_handler(CallbackQueryHandler(start_h.home_cb, pattern=r"^home$"))
    application.add_handler(CallbackQueryHandler(start_h.help_cb, pattern=r"^help$"))
    application.add_handler(CallbackQueryHandler(start_h.about_cb, pattern=r"^about$"))
    application.add_handler(CallbackQueryHandler(start_h.search_hint_cb, pattern=r"^search_hint$"))

    application.add_handler(CallbackQueryHandler(myfiles_h.myfiles_cb, pattern=r"^myfiles_\d+$"))
    application.add_handler(CallbackQueryHandler(myfiles_h.favs_cb, pattern=r"^favs_\d+$"))
    application.add_handler(CallbackQueryHandler(myfiles_h.recent_cb, pattern=r"^recent_\d+$"))

    application.add_handler(CallbackQueryHandler(callbacks_h.open_file_cb, pattern=r"^open_"))
    application.add_handler(CallbackQueryHandler(callbacks_h.get_file_cb, pattern=r"^get_"))
    application.add_handler(CallbackQueryHandler(callbacks_h.fav_cb, pattern=r"^fav_"))
    application.add_handler(CallbackQueryHandler(callbacks_h.delete_cb, pattern=r"^del_"))
    application.add_handler(CallbackQueryHandler(callbacks_h.rename_cb, pattern=r"^ren_"))

    return application


def main():
    keep_alive()  # starts a tiny web server so Render keeps the service alive
    application = build_application()
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("🛑 Bot stopped.")


if __name__ == "__main__":
    main()
