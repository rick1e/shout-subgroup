from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.models import UserModel
from shout_subgroup.repository import (
    find_all_users_in_group_chat,
    find_group_chat_by_telegram_group_chat_id,
    insert_user,
    insert_group_chat
)


async def add_user_to_group_chat(db: Session, chat: Chat, current_user: UserModel) -> UserModel | None:
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)

    if not group_chat:
        group_chat = await insert_group_chat(db, chat)

    all_users = await find_all_users_in_group_chat(db, chat.id)

    # Telegram usernames are case-insensitive,
    # but we're lowercasing these for consistency in string comparisons
    usernames_in_group_chat = [user.username.lower() for user in all_users]
    if current_user.username.lower() not in usernames_in_group_chat:
        added_user = await insert_user(db, current_user)
        group_chat.users.append(added_user)
        db.add(group_chat)
        db.commit()
        db.refresh(added_user)
        return added_user

    return None


async def listen_for_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = UserModel(
        telegram_user_id=update.message.from_user.id,
        username=update.message.from_user.username,
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name)

    maybe_added_user = await add_user_to_group_chat(session, update.effective_chat, current_user)
    # TODO: Add message like "The bot has recognized John Doe"
    return
