import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

from shout import shout_handler
from modify_subgroup import subgroup_handler
from shout_subgroup.list_subgroup import list_subgroup_handler

# Your bot's token
load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("shout", shout_handler))
    app.add_handler(CommandHandler("group", subgroup_handler))
    app.add_handler(CommandHandler("list", list_subgroup_handler))

    app.run_polling()


if __name__ == '__main__':
    main()
