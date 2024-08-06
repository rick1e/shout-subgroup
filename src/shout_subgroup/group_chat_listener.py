from sqlalchemy.orm import Session
from telegram import Update, Chat, User as TelegramUser
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.models import UserModel
from shout_subgroup.repository import (
    find_all_users_in_group_chat,
    find_group_chat_by_telegram_group_chat_id,
    insert_user,
    insert_group_chat
)


async def add_user_to_group_chat(db: Session, chat: Chat, current_user: TelegramUser) -> UserModel | None:
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)

    if not group_chat:
        group_chat = await insert_group_chat(
            db,
            chat.id,
            chat.title,
            chat.description if hasattr(chat, 'description') else ""
        )

    all_users = await find_all_users_in_group_chat(db, chat.id)

    # Telegram usernames are case-insensitive,
    # but we're lowercasing these for consistency in string comparisons
    usernames_in_group_chat = [user.username.lower() for user in all_users]
    if current_user.username.lower() not in usernames_in_group_chat:
        return await insert_new_user_into_group_chat(
            db,
            group_chat,
            current_user.id,
            current_user.username,
            current_user.first_name,
            current_user.last_name
        )

    return None


async def insert_new_user_into_group_chat(
        db,
        group_chat,
        user_id,
        username,
        first_name,
        last_name
) -> UserModel:
    """
    Inserts a user into an existing group chat.
    It's the caller's responsibility to ensure the group chat already.
    :param db:
    :param group_chat:
    :param user_id:
    :param username:
    :param first_name:
    :param last_name:
    :return:
    """

    added_user = await insert_user(
        db,
        user_id,
        username,
        first_name,
        last_name
    )

    group_chat.users.append(added_user)
    db.add(group_chat)
    db.commit()
    db.refresh(added_user)
    return added_user


async def listen_for_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await add_user_to_group_chat(session, update.effective_chat, update.message.from_user)
    # TODO: Think about adding message like "The bot has recognized John Doe"
    return
