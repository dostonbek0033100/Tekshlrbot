from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8766627088:AAHJAxw6qM9jy_O2T1pudmobV1dG4CFD398"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Moderator bot ishlayapti!\n\n"
        "✅ @user_ akkauntlar avtomatik o'chiriladi.\n"
        "🛡 Guruh himoyasi yoqilgan."
    )


async def check_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Kirdi xabarini o'chirish
    try:
        await update.message.delete()
    except:
        pass

    for user in update.message.new_chat_members:

        username = (user.username or "").lower()

        if username.startswith("user_"):
            try:
                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=user.id
                )

            except Exception as e:
                print(e)


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        check_new_user
    )
)

print("✅ Bot ishga tushdi")

app.run_polling()
