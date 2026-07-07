import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8766627088:AAHJAxw6qM9jy_O2T1pudmobV1dG4CFD398"

# Spam so'zlar
BAD_WORDS = [
    "18", "18+", "porn", "sex", "xxx",
    "onlyfans", "adult", "escort",
    "nude", "hot", "video", "girls"
]

# Reklama havolalari
BAD_LINKS = [
    "http://",
    "https://",
    "t.me/",
    "telegram.me/",
    ".com",
    ".net",
    ".xyz",
    ".vip",
    ".top",
    ".click"
]

# Ban qilinmaydigan admin ID lar
WHITELIST = [
    # 123456789,
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Moderator bot ishlayapti."
    )


def is_spam(username, fullname, text=""):
    username = (username or "").lower()
    fullname = (fullname or "").lower()
    text = (text or "").lower()

    # @user_ bilan boshlansa
    if username.startswith("user_"):
        return True

    # user_xxxxxxxx ko'rinishi
    if re.fullmatch(r"user_[a-z0-9]{8,12}", username):
        return True

    # Ism yoki username
    for word in BAD_WORDS:
        if word in username:
            return True
        if word in fullname:
            return True
        if word in text:
            return True

    # Link
    for link in BAD_LINKS:
        if link in text:
            return True

    return False
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # "Guruhga qo'shildi" xabarini o'chirish
    try:
        await update.message.delete()
    except:
        pass

    for user in update.message.new_chat_members:

        # Adminlarni o'tkazib yuborish
        if user.id in WHITELIST:
            continue

        if is_spam(user.username, user.full_name):

            try:
                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=user.id
                )

                await context.bot.send_message(
                    update.effective_chat.id,
                    f"🚫 @{user.username or user.first_name} avtomatik ban qilindi."
                )

            except Exception as e:
                print(e)


async def left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # "Guruhni tark etdi" xabarini o'chirish
    try:
        await update.message.delete()
    except:
        pass


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user

    # Adminlarni tekshirmaslik
    if user.id in WHITELIST:
        return

    text = update.message.text or ""

    if is_spam(user.username, user.full_name, text):

        try:
            await update.message.delete()
        except:
            pass

        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id
            )
        except Exception as e:
            print(e)
        async def check_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    caption = update.message.caption or ""

    if user.id in WHITELIST:
        return

    if is_spam(user.username, user.full_name, caption):
        try:
            await update.message.delete()
        except:
            pass

        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id
            )
        except Exception as e:
            print(e)


app = Application.builder().token(TOKEN).build()

# /start
app.add_handler(CommandHandler("start", start))

# Guruhga qo'shilganlar
app.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member)
)

# Guruhdan chiqqanlar
app.add_handler(
    MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member)
)

# Matnli xabarlar
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_message)
)

# Rasm + caption
app.add_handler(
    MessageHandler(filters.PHOTO, check_photo)
)

print("✅ Moderator bot ishga tushdi...")

app.run_polling(allowed_updates=Update.ALL_TYPES)
