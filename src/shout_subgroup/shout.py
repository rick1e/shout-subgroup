import logging
from typing import Sequence

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from shout_subgroup.database import get_database
from shout_subgroup.exceptions import NotGroupChatError, GroupChatDoesNotExistError
from shout_subgroup.models import UserModel
from shout_subgroup.repository import find_all_users_in_group_chat, find_all_users_in_subgroup, \
    find_group_chat_by_telegram_group_chat_id
from shout_subgroup.utils import is_group_chat, create_mention_from_user

logger = logging.getLogger(__name__)


async def shout_subgroup_members(db: Session, telegram_chat_id: int, subgroup_name: str) -> str:
    if not await is_group_chat(telegram_chat_id):
        msg = f"Can't shout subgroup members because telegram chat id {telegram_chat_id} is not a group chat."
        logger.info(msg)
        raise NotGroupChatError(msg)

    group_chat = await find_group_chat_by_telegram_group_chat_id(db, telegram_chat_id)
    if not group_chat:
        msg = f"Group chat with telegram_chat_id: {telegram_chat_id} was not found. "
        logger.info(msg)
        raise GroupChatDoesNotExistError(msg)

    subgroup_members = await find_all_users_in_subgroup(db, group_chat.group_chat_id, subgroup_name)

    if not subgroup_members:
        logger.info(f"Attempted to shout subgroup '{subgroup_name}' in telegram chat id: {telegram_chat_id} members, but there are no members.")
        return f"'{subgroup_name}' subgroup has no members, use /group to add members."

    message = create_message_to_mention_members(subgroup_members)
    return message


async def shout_all_members(db: Session, telegram_group_chat_id: int) -> str:
    group_chat_members = await find_all_users_in_group_chat(db, telegram_group_chat_id)

    if not group_chat_members:
        logger.info(f"Attempted to shout all members in telegram chat id '{telegram_group_chat_id}' but there are no members.")
        return "I don't know any members in this chat. If you want me to register someone ask them to send a message."

    message = create_message_to_mention_members(group_chat_members)
    return message


def create_message_to_mention_members(members: Sequence[UserModel]) -> str:
    message = ""
    for member in members:
        message += create_mention_from_user(member) + " "

    message = escape_markdown(message)
    return message


async def shout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles alerting members in group chats and subgroups.
    This function should not handle business logic,
    or storing data. It will delegate that responsibility
    to other functions. Similar to controllers from the MVC pattern.
    :param update:
    :param context:
    :return:
    """
    args = context.args
    db_session = get_database()

    with db_session.begin() as session:
        telegram_chat_id = update.effective_chat.id

        if len(args) == 1:
            subgroup_name = args[0]
            message = await shout_subgroup_members(session, telegram_chat_id, subgroup_name)

            await update.message.reply_text(message, parse_mode='markdown')
            return

        else:
            message = await shout_all_members(session, telegram_chat_id)
            await update.message.reply_text(message, parse_mode='markdown')
            return
