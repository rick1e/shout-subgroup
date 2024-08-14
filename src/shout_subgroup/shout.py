import logging
from typing import Sequence

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.exceptions import NotGroupChatError, GroupChatDoesNotExistError
from shout_subgroup.models import UserModel
from shout_subgroup.repository import find_all_users_in_group_chat, find_all_users_in_subgroup, \
    find_group_chat_by_telegram_group_chat_id
from shout_subgroup.utils import is_group_chat


async def shout_subgroup_members(db: Session, telegram_chat_id: int, subgroup_name: str) -> str:

    if not await is_group_chat(telegram_chat_id):
        msg = f"Can't create subgroup because telegram chat id {telegram_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    group_chat = await find_group_chat_by_telegram_group_chat_id(db, telegram_chat_id)
    if not group_chat:
        msg = f"Group chat with telegram_chat_id: {telegram_chat_id} was not found. "
        logging.info(msg)
        raise GroupChatDoesNotExistError(msg)

    all_members = await find_all_users_in_subgroup(db, group_chat.group_chat_id, subgroup_name)
    message = create_message_to_mention_members(all_members)
    return message


async def shout_all_members(db: Session, telegram_group_chat_id: int) -> str:
    all_members = await find_all_users_in_group_chat(db, telegram_group_chat_id)
    message = create_message_to_mention_members(all_members)
    return message


def mention_user(user: UserModel) -> str:
    mention = ""
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"[{user.first_name}](tg://user?id={user.telegram_user_id})"

    return mention


def create_message_to_mention_members(members: Sequence[UserModel]) -> str:
    message = ""
    for member in members:
        message += mention_user(member) + " "

    message = escape_special_characters(message)
    return message

def escape_special_characters(message: str):
    # TODO: add other special characters
    return message.replace("_","\\_")

async def shout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args

    if len(args) == 1:
        message = await shout_subgroup_members(session, args[0])
        await update.message.reply_text(message, parse_mode='markdown')
    else:
        message = await shout_all_members(session, update.effective_chat.id)
        await update.message.reply_text(message, parse_mode='markdown')
