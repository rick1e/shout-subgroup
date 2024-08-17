import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, filters, MessageHandler

from group_chat_listener import listen_for_messages_handler, listen_for_new_member_handler, \
    listen_for_left_member_handler
from modify_subgroup import subgroup_handler
from shout_subgroup.remove_subgroup_members import remove_subgroup_member_handler
from shout import shout_handler
from shout_subgroup.delete_subgroup import remove_subgroup_handler
from shout_subgroup.list_subgroup import list_subgroup_handler

from shout_subgroup.database import configure_database

load_dotenv()
TOKEN = os.getenv('TELEGRAM_API_KEY')


def main() -> None:

    if not configure_database():
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("shout", shout_handler))
    app.add_handler(CommandHandler("group", subgroup_handler))
    app.add_handler(CommandHandler("list", list_subgroup_handler))
    app.add_handler(CommandHandler("kick", remove_subgroup_member_handler))
    app.add_handler(CommandHandler("delete", remove_subgroup_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), listen_for_messages_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, listen_for_new_member_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, listen_for_left_member_handler))

    app.run_polling()


if __name__ == '__main__':
    main()
