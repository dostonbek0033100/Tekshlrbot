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
from telegram.helpers import escape_markdown

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable topilmadi!")

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
    "xxx", "adult", "18+",
]

# Soxta barolarni (false positive) oldini olish uchun
# "word boundary" bilan ishlaydigan regex'lar
def _build_word_regexes(words: list[str]) -> dict[str, "re.Pattern"]:
    pattern_map = {}
    for w in words:
        w_lower = w.lower()
        if re.fullmatch(r"[a-z0-9 ]+", w_lower):
            pattern_map[w_lower] = re.compile(
                r"(?<![a-z0-9])" + re.escape(w_lower) + r"(?![a-z0-9])"
            )
        else:
            pattern_map[w_lower] = re.compile(re.escape(w_lower))
    return pattern_map

SPAM_REGEXES = _build_word_regexes(SPAM_WORDS)

# ============================================================
# BAN QOIDALARI
# ============================================================
def should_ban(user) -> tuple[bool, str]:
    """Ism/username'da 'admin' bor bo'lsa yoki user_ bilan boshlansa — ban."""
    username = (user.username or "").lower().strip()
    full_name = f"{user.first_name or ''} {user.last_name or ''}".lower().strip()

    if username.startswith("user_"):
        return True, "username user_ bilan boshlanadi"
    if "admin" in username:
        return True, f"username'da 'admin' bor: @{username}"
    if "admin" in full_name:
        return True, f"ismda 'admin' bor: {full_name or 'noma'lum'}"
    return False, ""

# ============================================================
# SPAM TEKSHIRISH
# ============================================================
def contains_spam(text: str) -> list[str]:
    text_lower = text.lower()
    return [word for word, rgx in SPAM_REGEXES.items() if rgx.search(text_lower)]

# ============================================================
# RENDER HEALTH SERVER
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("ModerBot ishlayapti!".encode("utf-8"))
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
# ADMINLARGA BILDIRIM
# ============================================================
async def notify_admins(context: ContextTypes.DEFAULT_TYPE, chat_title: str, user, reason: str):
    """Barcha adminlarga ban haqida xabar yuboradi."""
    if not user:
        return
    username_text = f"@{user.username}" if user.username else "username yo'q"
    text = (
        f"🚫 *{escape_markdown(chat_title or 'noma'lum guruh')}* dan "
        f"{escape_markdown(username_text)} banlandi\n"
        f"📌 Sabab: {escape_markdown(reason)}\n"
        f"👤 Ism: {escape_markdown(user.first_name or 'noma'lum')}\n"
        f"🆔 ID: {user.id}"
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
        "🛡 Ismida yoki username'ida 'admin' bor akkauntlar bloklanadi.\n"
        "🛡 Spam so'zlar yozgan foydalanuvchilar bloklanadi."
    )

# ============================================================
# SPAM XABARLARNI TEKSHIRISH
# ============================================================
async def check_spam_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    if not message.chat or message.chat.type not in ("group", "supergroup"):
        return
    if not message.from_user:
        return
    if message.from_user.id in ADMIN_IDS:
        return
    text = message.text or message.caption or ""
    if not text:
        return

    spam_found = contains_spam(text)
    if spam_found:
        reason = f"spam so'zlar: {', '.join(spam_found)}"
        await handle_violation(update, context, reason)

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
        print("====================================")
        print("🚫 BAN QILINDI (doimiy)")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print("====================================")
    except Exception as e:
        print(f"❌ Ban qilishda xatolik: {e}")
        print("⚠️  Ehtimol bot guruhda ADMIN emas yoki 'Ban users' huquqiga ega emas!")
        return

    # 3. ADMINLARGA BILDIRIM
    await notify_admins(context, chat.title, user, reason)

    # 4. Banlangan foydalanuvchi ga shaxsiy xabar
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"⛔ Siz {chat.title} guruhidan ban qilindingiz.\n"
                f"📌 Sabab: {reason}\n"
                f"❓ Nega ban qilganini bilib olish uchun admin bilan murojaat qiling."
            )
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

    username_text = f"@{user.username}" if user.username else "username yo'q"

    try:
        await context.bot.ban_chat_member(
            chat_id=chat_member.chat.id,
            user_id=user.id
        )
        print("====================================")
        print("🚫 BAN QILINDI")
        print(f"👤 Ism: {user.first_name}")
        print(f"🔗 Username: {username_text}")
        print(f"🆔 ID: {user.id}")
        print(f"📌 Sabab: {reason}")
        print("====================================")
    except Exception as e:
        print(f"❌ Ban qilishda xatolik: {e}")
        print("⚠️  Ehtimol bot guruhda ADMIN emas yoki 'Ban users' huquqiga ega emas!")
        return

    # Adminlarga bildirim
    await notify_admins(context, chat_member.chat.title, user, reason)

    # Banlangan foydalanuvchiga shaxsiy xabar
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"⛔ Siz {chat_member.chat.title} guruhidan ban qilindingiz.\n"
                f"📌 Sabab: {reason}\n"
                f"❓ Nega ban qilganini bilib olish uchun admin bilan murojaat qiling."
            )
        )
    except Exception:
        pass

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
    print("   2. ism/username'da 'admin' so'zi bo'lsa")
    print(f"   3. spam so'zlar: {len(SPAM_WORDS)} ta")
    print(f"   👤 Admin ID: {ADMIN_IDS}")
    print("")
    print("⚠️ ESLATMA: bot har bir guruhda ADMIN bo'lib,")
    print("   'Ban users' huquqiga ega bo'lishi kerak!")
    print("")
    print("📡 Telegram polling boshlandi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
