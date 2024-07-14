import logging
from typing import Type

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.exceptions import NotGroupChatError, SubGroupDoesNotExistsError
from shout_subgroup.models import SubgroupModel, UserModel
from shout_subgroup.repository import find_all_subgroups_in_group_chat, \
    find_subgroup_by_telegram_group_chat_id_and_subgroup_name, find_all_users_in_subgroup
from shout_subgroup.utils import is_group_chat


async def _handle_list_subgroups(update: Update, db: Session, telegram_group_chat_id: int):
    """
       Handles the listing of subgroups for a given Telegram group chat.

       Args:
           update (Update): The update object from the Telegram bot.
           db (Session): The SQLAlchemy session object.
           telegram_group_chat_id (int): The ID of the Telegram group chat.

       Returns:
           List[str]: A list of subgroup names.

       Raises:
           NotGroupChatError: If the provided chat ID is not a group chat.
           SubGroupExistsError: If a subgroup already exists for the provided chat ID and name.
       """
    subgroups = await list_subgroups(db, telegram_group_chat_id)

    if not subgroups:
        await update.message.reply_text(f"There are no subgroups in this chat")
        return

    # "mock-subgroup-1, mock-subgroup-2, mock-subgroup-3"
    subgroups_names = [sub.name for sub in subgroups]
    joined_subgroup_names = ", ".join(subgroups_names)

    await update.message.reply_text(f"Here are the subgroups for this chat: {joined_subgroup_names}")
    return


async def list_subgroups(db: Session, telegram_group_chat_id: int) -> list[Type[SubgroupModel]]:
    # Guard Clauses
    if not await is_group_chat(telegram_group_chat_id):
        msg = f"Can't list subgroups because telegram chat id {telegram_group_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    # Get all the subgroups for the group chat
    subgroups = await find_all_subgroups_in_group_chat(db, telegram_group_chat_id)
    return subgroups


async def _handle_list_subgroup_members(update: Update, db: Session, telegram_group_chat_id: int, subgroup_name: str):
    await update.message.reply_text(f"MOCK SUBGROUP RESPONSE. Subgroup name = {subgroup_name}")
    pass


async def list_subgroup_members(db: Session, telegram_group_chat_id: int, subgroup_name: str) -> list[Type[UserModel]]:

    # Guard Clauses
    if not await is_group_chat(telegram_group_chat_id):
        msg = f"Can't list subgroups because telegram chat id {telegram_group_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    # If subgroup does not exist throw exception
    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_group_chat_id, subgroup_name)
    if not subgroup:
        msg = f"Subgroup: {subgroup_name} does not exist in telegram group chat: {telegram_group_chat_id}"
        logging.info(msg)
        raise SubGroupDoesNotExistsError(msg)

    # Get all the users for the subgroup
    users = await find_all_users_in_subgroup(db, subgroup.group_chat_id, subgroup_name)
    return users


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

    args = context.args
    chat_id = update.effective_chat.id
    subgroup_name = args[0] if len(args) == 1 else ""

    try:
        # If the subgroup name doesn't exist, we'll default to listing the subgroups
        if subgroup_name:
            await _handle_list_subgroup_members(update, session, chat_id, subgroup_name)
        else:
            await _handle_list_subgroups(update, session, chat_id)

    except NotGroupChatError:
        await update.message.reply_text("Sorry, you can only list subgroups in group chats.")
        return
    except SubGroupDoesNotExistsError:
        await update.message.reply_text(f"Subgroup {subgroup_name} does not exist.")
        return
