import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                b"ModerBot ishlayapti!"
            )

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():

    port = int(
        os.environ.get("PORT", 10000)
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"Health server {port}-portda ishga tushdi"
    )

    server.serve_forever()


# ============================================================
# /start
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    await update.message.reply_text(
        "🤖 ModerBot ishlayapti!\n\n"
        "🛡 @user_... username'lar bloklanadi.\n"
        "🛡 Ismi admin + raqam bo'lgan akkauntlar bloklanadi."
    )


# ============================================================
# BAN QOIDALARI
# ============================================================

def should_ban(user) -> tuple[bool, str]:

    username = user.username or ""
    first_name = user.first_name or ""

    username_lower = username.lower().strip()
    first_name_lower = first_name.lower().strip()

    # ========================================================
    # 1. USERNAME: user_ bilan boshlansa
    #
    # Misollar:
    # @user_123
    # @user_45678
    # ========================================================

    if username_lower.startswith("user_"):

        return (
            True,
            "username user_ bilan boshlanadi"
        )

    # ========================================================
    # 2. PROFIL ISMI: admin + faqat raqamlar
    #
    # Misollar:
    # admin1
    # admin12
    # admin133
    # admin98765
    #
    # Faqat First Name tekshiriladi.
    # Username qanday bo'lishidan qat'i nazar BAN qilinadi.
    # ========================================================

    if re.fullmatch(
        r"admin\d+",
        first_name_lower
    ):

        return (
            True,
            "profil ismi admin + raqamlar"
        )

    # ========================================================
    # BAN EMAS
    # ========================================================

    return False, ""


# ============================================================
# YANGI A'ZONI TEKSHIRISH
# ============================================================

async def check_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_member = update.chat_member

    if not chat_member:
        return

    old_status = (
        chat_member.old_chat_member.status
    )

    new_status = (
        chat_member.new_chat_member.status
    )

    # Faqat yangi qo'shilganlar
    if new_status not in (
        "member",
        "restricted"
    ):
        return

    # Oldin guruhda bo'lmagan bo'lishi kerak
    if old_status not in (
        "left",
        "kicked",
        "banned"
    ):
        return

    user = chat_member.new_chat_member.user

    # ========================================================
    # BAN TEKSHIRISH
    # ========================================================

    ban, reason = should_ban(user)

    if not ban:
        return

    try:

        await context.bot.ban_chat_member(
            chat_id=chat_member.chat.id,
            user_id=user.id
        )

        username_text = (
            f"@{user.username}"
            if user.username
            else "username yo'q"
        )

        print(
            "===================================="
        )

        print(
            f"🚫 BAN QILINDI"
        )

        print(
            f"👤 Ism: {user.first_name}"
        )

        print(
            f"🔗 Username: {username_text}"
        )

        print(
            f"🆔 ID: {user.id}"
        )

        print(
            f"📌 Sabab: {reason}"
        )

        print(
            "===================================="
        )

    except Exception as e:

        print(
            f"❌ Ban qilishda xatolik: {e}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("====================================")
    print("🤖 ModerBot ishga tushmoqda...")
    print("====================================")

    # Render health server
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # Telegram application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    # Yangi a'zolarni kuzatish
    application.add_handler(
        ChatMemberHandler(
            check_new_member,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    print("✅ ModerBot tayyor!")
    print("")
    print("🛡 BAN QOIDALARI:")
    print("   1. username: user_...")
    print("   2. profil ismi: admin + raqamlar")
    print("")
    print("📡 Telegram polling boshlandi...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
