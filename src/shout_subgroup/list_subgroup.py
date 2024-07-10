from telegram import Update
from telegram.ext import ContextTypes


async def list_subgroups() -> str:
    # Get all the subgroups for the group chat

    # Transform into string

    return "mock-subgroup-1, mock-subgroup-2, mock-subgroup-3"


async def list_subgroup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the list subgroup command.
    This function should not handle business logic,
    or storing data. It will delegate that responsibility
    to other functions. Similar to controllers from the MVC pattern.
    :param update:
    :param context:
    :return:
    """
    subgroups = await list_subgroups(update.effective_chat.id)
    await update.message.reply_text(f"Here are the subgroups for this chat: {subgroups}")
    return
