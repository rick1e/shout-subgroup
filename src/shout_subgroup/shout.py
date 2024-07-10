from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes
from typing import Sequence
from shout_subgroup.models import UserModel
from shout_subgroup.repository import find_all_users_in_group_chat
from shout_subgroup.database import session
from typing import Sequence

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.models import UserModel
from shout_subgroup.repository import find_all_users_in_group_chat


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

    return message


async def shout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.effective_user.username)
    message = await shout_all_members(session, update.effective_chat.id)
    await update.message.reply_text(message, parse_mode='markdown')
