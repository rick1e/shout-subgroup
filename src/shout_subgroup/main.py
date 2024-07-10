import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from shout import shout_handler
from subgroup import create_subgroup_handler
from shout_subgroup.models import UserModel
from shout_subgroup.database import session




# Your bot's token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("shout", shout_handler))
    app.add_handler(CommandHandler("group", create_subgroup_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
