import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)


# ============================================================
# SOZLAMALAR
# ============================================================

TOKEN = os.getenv("8766627088:AAHJAxw6qM9jy_O2T1pudmobV1dG4CFD398")

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Render → Environment bo‘limiga "
        "BOT_TOKEN qo‘shing."
    )


# ============================================================
# RENDER HEALTH CHECK SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ["/", "/health"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Telegram bot ishlayapti!")

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Har bir health-check logni chiqarib tashlamaymiz
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Health server ishga tushdi: 0.0.0.0:{port}")

    server.serve_forever()


# ============================================================
# /start
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message:
        await update.message.reply_text(
            "🤖 Moderator bot ishlayapti!\n"
            "🛡 @user_ akkauntlar bloklanadi."
        )


# ============================================================
# YANGI A'ZONI TEKSHIRISH
# ============================================================

async def member_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.chat_member:
        return

    old = update.chat_member.old_chat_member
    new = update.chat_member.new_chat_member

    # Faqat yangi kirganlarni tekshirish
    if old.status in ["left", "kicked"] and new.status == "member":

        user = new.user
        username = (user.username or "").lower()

        print("KIRDI:", username)

        # username user_ bilan boshlansa bloklash
        if username.startswith("user_"):

            try:

                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=user.id
                )

                print("BAN:", username)

            except Exception as e:

                print(
                    f"BAN XATOSI [{username}]: {e}"
                )


# ============================================================
# ASOSIY DASTUR
# ============================================================

def main():

    # Render uchun HTTP serverni alohida thread'da ishga tushiramiz
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # Telegram bot
    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Yangi a'zolarni tekshirish
    app.add_handler(
        ChatMemberHandler(
            member_check,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    print("========================================")
    print("🤖 Moderator bot ishga tushdi")
    print("🛡 @user_ akkauntlar bloklanadi")
    print("🌐 Render health server ishlayapti")
    print("========================================")

    # Telegram polling
    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
