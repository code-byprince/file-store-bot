import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ---- Get this from @BotFather on Telegram ----
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # ---- MongoDB (from https://cloud.mongodb.com free cluster) ----
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DB_NAME = os.environ.get("DB_NAME", "FileStoreBot")

    # ---- Private channel where the bot dumps every uploaded file ----
    # Add the bot as ADMIN in this channel first. Use the channel's
    # numeric id, e.g. -1001234567890
    DB_CHANNEL = int(os.environ.get("DB_CHANNEL", "0"))

    # ---- Admins (comma separated Telegram user ids) ----
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split(",") if x.strip()]

    # ---- Force Subscribe channel(s), comma separated usernames (no @) ----
    FORCE_SUB_CHANNELS = [
        x.strip() for x in os.environ.get("FORCE_SUB_CHANNELS", "").split(",") if x.strip()
    ]

    # ---- Misc ----
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")  # without @
    START_PIC = os.environ.get("START_PIC", "")
    PORT = int(os.environ.get("PORT", "8080"))

    WELCOME_TEXT = os.environ.get(
        "WELCOME_TEXT",
        "👋 Welcome, {mention}!\n\nMain ek advanced file storage bot hoon.\n"
        "Mujhe koi bhi file bhejo, main uski permanent link bana dunga.",
    )
