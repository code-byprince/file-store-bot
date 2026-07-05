# 📁 Advanced File Storage Bot v2 — with Real Colored Buttons

Ye version **python-telegram-bot (v22.7)** library pe based hai — Pyrogram nahi. Isse:

1. **Real colored buttons** milte hain (🔴 Delete = red, 🟢 Favorite = green, 🔵 Rename/Download = blue) — Telegram ke naye Bot API 9.4 feature ka use karke.
2. Ab sirf **BOT_TOKEN** chahiye — API_ID / API_HASH ki zaroorat nahi.
3. "Peer id invalid" wala bug bhi khatam ho gaya (Bot API channel access alag tarike se kaam karta hai, MTProto peer-cache ka jhanjhat nahi).

⚠️ **Important:** Colored buttons sirf **latest Telegram app** (updated after Feb 2026) mein dikhte hain. Purane Telegram version wale users ko normal (bina color) buttons dikhenge — koi crash nahi hoga, bas color show nahi hoga unke liye.

---

## 🗂 File Structure

```
FileStoreBotV2/
├── main.py                  # Entry point — sab handlers yahan register hote hain
├── config.py                 # Environment variables
├── keep_alive.py              # Render 24/7 uptime ke liye
├── requirements.txt
├── Procfile
├── render.yaml
├── .python-version
├── .env.example
├── database/
│   └── db.py                   # MongoDB queries (unchanged)
├── utils/
│   └── helpers.py                # human_size, uptime, link encode/decode (unchanged)
└── handlers/
    ├── start.py                    # /start, /help, /about, /privacy, force-subscribe
    ├── upload.py                     # File upload + colored action buttons
    ├── myfiles.py                     # My Files, Search, Favorites, Recent, Stats
    ├── callbacks.py                     # Open/Download/Favorite/Delete/Rename actions
    └── admin.py                          # Admin panel, broadcast, ban, channel-ID detector
```

---

## ⚙️ Setup (simpler than before!)

1. **BOT_TOKEN:** [@BotFather](https://t.me/BotFather) se `/newbot` karke lo.
2. **DB_CHANNEL:** Ek private channel banao, bot ko admin banao. Fir us channel mein koi text message bhejo, use apne bot ki DM mein **forward** karo — bot khud exact ID bata dega.
3. **MONGO_URI:** MongoDB Atlas se connection string (pehle jaisa hi).
4. **ADMINS:** Apni Telegram user ID.

`API_ID` / `API_HASH` ab **zaroorat nahi hai** — isse setup thoda simple ho gaya.

---

## 🐙 GitHub Par Migrate Karna (purani repo se)

Kyunki poora folder structure aur files badal gayi hain, sabse safe tarika hai: **purani repo ka content pura hata ke naya daal do.**

```bash
git clone https://github.com/code-byprince/file-store-bot.git
cd file-store-bot

# Purana sab kuch hata do (sirf .git rehne do)
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

# Ab is FileStoreBotV2.zip ko extract karke, uske ANDAR ki saari files/folders
# is file-store-bot folder ke andar copy karo (database/, handlers/, utils/ samet)

git add .
git commit -m "Migrate to python-telegram-bot with colored buttons"
git push
```

## ☁️ Render Par Update Karna

1. **Environment tab** mein jaake:
   - `API_ID` aur `API_HASH` variables ko **delete kar do** (ab zaroorat nahi, chahe rehne bhi do to koi dikkat nahi)
   - baaki sab (`BOT_TOKEN`, `MONGO_URI`, `DB_NAME`, `DB_CHANNEL`, `ADMINS`, `FORCE_SUB_CHANNELS`, `PORT`) same rakho
2. **Manual Deploy → Deploy latest commit**
3. Logs mein `🤖 Bot is starting...` dikhna chahiye, koi traceback nahi.

---

## ✅ Colored Buttons Kahan Dikhenge

- 🔴 **Delete** button — red
- 🟢 **Favorite** button — green
- 🔵 **Rename / Download / Share / Next** buttons — blue
- **Home / Back / Prev** — normal (neutral, no color) — kam-important actions ke liye jaan-boojh kar plain rakha hai

Agar tumhara Telegram app purana hai, to ye same buttons bina color ke dikhenge — bot phir bhi bilkul normal kaam karega.
