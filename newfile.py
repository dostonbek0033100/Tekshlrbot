from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes
)

TOKEN = "8766627088:AAHJAxw6qM9jy_O2T1pudmobV1dG4CFD398"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Moderator bot ishlayapti!\n"
        "🛡 @user_ akkauntlar bloklanadi."
    )


async def member_check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    old = update.chat_member.old_chat_member
    new = update.chat_member.new_chat_member

    # Faqat yangi kirganlarni tekshirish
    if old.status in ["left", "kicked"] and new.status == "member":

        user = new.user
        username = (user.username or "").lower()

        print("KIRDI:", username)

        if username.startswith("user_"):

            try:
                await context.bot.ban_chat_member(
                    update.effective_chat.id,
                    user.id
                )

                print("BAN:", username)

            except Exception as e:
                print(e)


app = Application.builder().token(TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    ChatMemberHandler(
        member_check,
        ChatMemberHandler.CHAT_MEMBER
    )
)


print("Bot ishga tushdi")

app.run_polling(
    allowed_updates=Update.ALL_TYPES
)
