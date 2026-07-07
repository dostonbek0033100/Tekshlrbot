import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "YANGI_BOT_TOKENINGIZ"

# Ruxsat berilgan admin ID lar
WHITELIST = [
    # Masalan: 123456789
]

# Spam so'zlar
BAD_WORDS = [
    "18", "18+", "porn", "sex", "xxx",
    "onlyfans", "adult", "escort",
    "nude", "hot"
]

# Reklama linklari
BAD_LINKS = [
    "http://",
    "https://",
    "t.me/",
    "telegram.me/",
    ".com",
    ".xyz",
    ".top",
    ".vip"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Assalomu alaykum!\n\n"
        "✅ Moderator Bot ishlayapti.\n"
        "🛡 Guruh himoyasi yoqilgan.\n\n"
        "• @user_ akkauntlar tekshiriladi.\n"
        "• Spam xabarlar o'chiriladi.\n"
        "• Reklama va 18+ kontent bloklanadi.\n\n"
        "🚀 Bot faol!"
    )


def is_spam(username, fullname, text=""):
    username = (username or "").lower()
    fullname = (fullname or "").lower()
    text = (text or "").lower()

    # user_ bilan boshlansa
    if username.startswith("user_"):
        return True

    # user_xxxxx ko'rinishida bo'lsa
    if re.fullmatch(r"user_[a-z0-9]{8,12}", username):
        return True

    # So'z tekshirish
    for word in BAD_WORDS:
        if word in username:
            return True
        if word in fullname:
            return True
        if word in text:
            return True

    # Link tekshirish
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

        # Oq ro'yxatdagilar o'tadi
        if user.id in WHITELIST:
            continue

        if is_spam(user.username, user.full_name):

            try:
                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=user.id
                )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🚫 {user.first_name} spam sababli ban qilindi."
                )

            except Exception as e:
                print("Ban xatosi:", e)



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

    if is_spam(
        user.username,
        user.full_name,
        text
    ):

        try:
            await update.message.delete()
        except Exception as e:
            print("O'chirish xatosi:", e)

        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id
            )

        except Exception as e:
            print("Ban xatosi:", e)
async def check_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.effective_user

    if user.id in WHITELIST:
        return

    caption = update.message.caption or ""

    if is_spam(
        user.username,
        user.full_name,
        caption
    ):

        try:
            await update.message.delete()
        except:
            pass

        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user.id
            )
        except:
            pass



app = Application.builder().token(TOKEN).build()


# /start
app.add_handler(
    CommandHandler("start", start)
)


# Guruhga yangi kirganlar
app.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        new_member
    )
)


# Guruhdan chiqqanlar
app.add_handler(
    MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER,
        left_member
    )
)


# Oddiy matn xabarlar
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        check_message
    )
)


# Rasm va caption tekshirish
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        check_photo
    )
)


print("✅ Moderator bot ishga tushdi...")


app.run_polling(
    allowed_updates=Update.ALL_TYPES
)
