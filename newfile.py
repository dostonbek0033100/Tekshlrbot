import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")

# ============================================================
# ADMINLAR (Telegram ID)
# ============================================================
ADMIN_IDS = {1072547777}

# ============================================================
# SPAM SO'ZLAR RO'YXATI
# ============================================================
SPAM_WORDS = [
    "casino", "gambling", "bet", "pkr", "poker",
    "xy", "freelance", "work from home", "earn money",
    "click here", "free giveaway", "crypto airdrop",
    "join now", "limited time", "act fast",
    "💰", "📈", "🎰", "🏦", "💸",
    "http://", "https://", "bit.ly", "t.me/",
    "promo", "discount", "earn$", "make money",
    "double your", "guaranteed", "no risk",
    "xxx", "adult", "18+", "profilimda video bor",
]

BANNED_KEYWORDS = [
    "hack", "crack", "cheat", "bot farm",
]

# ============================================================
# BAN QOIDALARI
# ============================================================
def should_ban(user) -> tuple[bool, str]:
    username = user.username or ""
    first_name = user.first_name or ""
    username_lower = username.lower().strip()
    first_name_lower = first_name.lower().strip()

    if username_lower.startswith("user_"):
        return True, "username user_ bilan boshlanadi"

    if re.fullmatch(r"admin\d+", first_name_lower):
        return True, "profil ismi admin + raqamlar"

    return False, ""


# ============================================================
# SPAM TEKSHIRISH
# ============================================================
def contains_spam(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for word in SPAM_WORDS:
        if word.lower() in text_lower:
            found.append(word)
    return found


def contains_banned_keyword(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for word in BANNED_KEYWORDS:
        if word.lower() in text_lower:
            found.append(word)
    return found


# ============================================================
# RENDER HEALTH SERVER
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ModerBot ishlayapti!")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server {port}-portda ishga tushdi")
    server.serve_forever()


# ============================================================
# ADMINLARGA BILDIRIM (yangilangan format)
# ============================================================
async def notify_admins(context: ContextTypes.DEFAULT_TYPE, chat_title: str, user, reason: str):
    """Barcha adminlarga ban haqida xabar yuboradi."""
    username_text = f"@{user.username}" if user.username else "username yo'q"
    text = (
        f"🚫 *{chat_title}* dan {username_text} banlandi\n"
        f"📌 Sabab: {reason}\n"
        f"👤 Ism: {user.first_name}\n"
        f"🆔 ID: `{user.id}`"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode="Markdown"
            )
            print(f"📩 Admin {admin_id} ga bildirim yuborildi")
        except Exception as e:
            print(f"❌ Admin {admin_id} ga xabar yuborilmadi: {e}")


# ============================================================
# /start
# ============================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        "🤖 ModerBot ishlayapti!\n\n"
        "🛡 @user_... username'lar bloklanadi.\n"
        "🛡 Ismi admin + raqam bo'lgan akkauntlar bloklanadi.\n"
        "🛡 Spam so'zlar yozgan foydalanuvchilar bloklanadi."
    )


# ============================================================
# SPAM XABARLARNI TEKSHIRISH
# ============================================================
async def check_spam_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    if not message.chat or message.chat.type in ("private",):
        return

    if message.from_user and message.from_user.id in ADMIN_IDS:
        return

    text = message.text or ""
    if not text:
        return

    spam_found = contains_spam(text)
    banned_found = contains_banned_keyword(text)

    if spam_found:
        reason = f"spam so'zlar: {', '.join(spam_found)}"
        await handle_violation(update, context, reason)
        return

    if banned_found:
        reason = f"manxur so'zlar: {', '.join(banned_found)}"
        await handle_violation(update, context, reason)
        return


async def handle_violation(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str):
    user = update.message.from_user
    chat = update.message.chat
    message_id = update.message.message_id
    username_text = f"@{user.username}" if user.username else "username yo'q"

    if user.id in ADMIN_IDS:
        print(f"⚠️ Admin {user.first_name} tekshirildi: {reason}")
        return

    # 1. Xabarni O'CHIRISH
    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message_id
        )
        print(f"🗑 Xabar o'chirildi (ID: {message_id})")
    except Exception as e:
        print(f"❌ Xabar o'chirishda xatolik: {e}")

    # 2. Foydalanuvchini BAN qilish
    try:
        await context.bot.ban_chat_member(
            chat_id=chat.id,
            user_id=user.id
        )
        print(f"====================================")
        print(f"🚫 BAN QILINDI (doimiy)")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print(f"====================================")
    except Exception as e:
        print(f"❌ Ban qilishda xatolik: {e}")

    # 3. ADMINLARGA BILDIRIM (yangi format)
    await notify_admins(context, chat.title, user, reason)

    # 4. Foydalanuvchiga xabar berish
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"⛔ Siz {chat.title} guruhidan ban qilindingiz.\n"
                 f"📌 Sabab: {reason}\n"
                 f"❓ Nega ban qilindiğini bilib olish uchun admin bilan murojat qiling."
        )
    except Exception:
        pass


# ============================================================
# YANGI A'ZONI TEKSHIRISH
# ============================================================
async def check_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    if not chat_member:
        return

    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status

    if new_status not in ("member", "restricted"):
        return
    if old_status not in ("left", "kicked", "banned"):
        return

    user = chat_member.new_chat_member.user
    ban, reason = should_ban(user)
    if not ban:
        return

    try:
        await context.bot.ban_chat_member(
            chat_id=chat_member.chat.id,
            user_id=user.id
        )
        username_text = f"@{user.username}" if user.username else "username yo'q"
        print("====================================")
        print(f"🚫 BAN QILINDI")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print("====================================")
    except Exception as e:
        print(f"❌ Ban qilishda xatolik: {e}")


# ============================================================
# MAIN
# ============================================================
def main():
    print("====================================")
    print("🤖 ModerBot ishga tushmoqda...")
    print("====================================")

    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))

    application.add_handler(
        ChatMemberHandler(check_new_member, ChatMemberHandler.CHAT_MEMBER)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_spam_message)
    )

    print("✅ ModerBot tayyor!")
    print("")
    print("🛡 BAN QOIDALARI:")
    print("   1. username: user_...")
    print("   2. profil ismi: admin + raqamlar")
    print(f"   3. spam so'zlar: {len(SPAM_WORDS)} ta")
    print(f"   👤 Admin ID: 1072547777")
    print("")
    print("📡 Telegram polling boshlandi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
