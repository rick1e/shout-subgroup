import logging

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.exceptions import SubGroupDoesNotExistsError, NotGroupChatError
from shout_subgroup.repository import find_subgroup_by_telegram_group_chat_id_and_subgroup_name, delete_subgroup
from shout_subgroup.utils import is_group_chat


async def remove_subgroup(db: Session, telegram_chat_id: int, subgroup_name: str) -> bool:
    if not await is_group_chat(telegram_chat_id):
        msg = f"Can't kick members from subgroup because telegram chat id {telegram_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    # Find the subgroup
    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_chat_id, subgroup_name)
    if not subgroup:
        msg = f"Subgroup {subgroup_name} does not exist."
        logging.info(msg)
        raise SubGroupDoesNotExistsError(msg)

    # Perform the deletion
    is_deleted = await delete_subgroup(db, telegram_chat_id, subgroup_name)

    return is_deleted


async def remove_subgroup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles deleting subgroups from group chats.
    This function should not handle business logic,
    or storing data. It will delegate that responsibility
    to other functions. Similar to controllers from the MVC pattern.
    :param update:
    :param context:
    :return:
    """

    args = context.args

    # Quick guard clause
    if len(args) < 1:
        msg = "You didn't use this command correctly. Please type /delete <group_name>"
        await update.message.reply_text(msg)
        return

    subgroup_name = args[0]

    try:
        is_deleted = await remove_subgroup(session, update.effective_chat.id, subgroup_name)

        if is_deleted:
            await update.message.reply_text(f"Subgroup '{subgroup_name}' was deleted")
            return

        msg = (f"The remove_subgroup function returned {is_deleted}, when it should have returned True or throw an "
               f"exception.")
        logging.error(msg)

        raise RuntimeError(msg)

    except NotGroupChatError:
        await update.message.reply_text("Sorry, you can only create or modify subgroups in group chats.")
        return

    except SubGroupDoesNotExistsError:
        msg = f"I can't delete subgroup '{subgroup_name}' because it does not exist"
        await update.message.reply_text(msg)
        return

    except Exception:
        logging.exception("An unexpected exception occurred")
        await update.message.reply_text("Whoops 😅, something went wrong on our side.")
