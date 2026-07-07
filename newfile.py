from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8766627088:AAHJAxw6qM9jy_O2T1pudmobV1dG4CFD398"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Moderator bot ishlayapti!\n\n"
        "🛡 @user_ bilan boshlanadigan akkauntlar avtomatik chiqariladi."
    )


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    # Kirdi xabarini o'chirish
    try:
        await update.message.delete()
    except Exception as e:
        print("Delete:", e)

    for user in update.message.new_chat_members:

        username = (user.username or "").lower()

        print(
            "Yangi odam:",
            user.id,
            username,
            user.full_name
        )

        if username.startswith("user_"):

            try:
                # Ban qilish
                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=user.id
                )

                print("BAN:", username)

            except Exception as e:
                print("BAN xato:", e)



app = Application.builder().token(TOKEN).build()


app.add_handler(
    CommandHandler("start", start)
)


app.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        new_member
    )
)


print("✅ Bot ishga tushdi")

app.run_polling(
    allowed_updates=Update.ALL_TYPES
)
