import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from shout import shout_all_members
from shout_subgroup.models import UserModel
from shout_subgroup.database import session




# Your bot's token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'Hello {update.effective_user.first_name}')
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def shout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.effective_chat.id)
    message = await shout_all_members(session,update.effective_chat.id)
    await update.message.reply_text(message, parse_mode='markdown')

def main() -> None:
    print('Runninig ...')
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("shout", shout))

    app.run_polling()

if __name__ == '__main__':
    main()
