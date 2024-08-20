import logging

from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes

from shout_subgroup.exceptions import NotGroupChatError
from shout_subgroup.models import UserModel
from shout_subgroup.repository import (
    find_all_users_in_group_chat,
    find_all_subgroups_in_group_chat,
    find_users_by_usernames,
    find_group_chat_by_telegram_group_chat_id,
    insert_group_chat,
    add_user_to_group_chat as add_user_to_group_chat_repo
)
from shout_subgroup.utils import is_group_chat
from shout_subgroup.remove_subgroup_members import remove_users_from_existing_subgroup

from shout_subgroup.database import get_database


async def add_user_to_group_chat(db: Session, chat: Chat, current_user: UserModel) -> UserModel | None:
    if not await is_group_chat(chat.id):
        msg = f"Can't add user to group because telegram chat id {chat.id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    # Check if the group chat exists in our system, if not we need to add it
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)
    if not group_chat:
        group_chat = await insert_group_chat(db, chat.id, chat.title, chat.description)

    # Add the user to the group chat if they're not already in it
    all_users = await find_all_users_in_group_chat(db, chat.id)
    telegram_user_ids_in_group_chat = {user.telegram_user_id for user in all_users}

    if current_user.telegram_user_id not in telegram_user_ids_in_group_chat:
        return await add_user_to_group_chat_repo(db, group_chat, current_user)

    return None


async def remove_user_from_group_chat(db: Session, chat: Chat, current_user: UserModel) -> UserModel | None:
    if not await is_group_chat(chat.id):
        msg = f"Can't remove user from chat because telegram chat id {chat.id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)

    if not group_chat:
        return None

    users_to_be_removed = await find_users_by_usernames(db, {current_user.username})

    if len(users_to_be_removed) == 1:
        # Remove user from all subgroups as well
        await remove_user_from_all_group_chat_sub_groups(db, chat.id, users_to_be_removed[0])
        group_chat.users.remove(users_to_be_removed[0])
        db.commit()
        db.refresh(group_chat)
        return users_to_be_removed[0]

    return None


async def remove_user_from_all_group_chat_sub_groups(db: Session, telegram_group_chat_id: int, user: UserModel) -> None:
    subgroups = await find_all_subgroups_in_group_chat(db, telegram_group_chat_id)
    for subgroup in subgroups:
        await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup.name, {user.username})


async def listen_for_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles listening to messages sent by users.

    The handler listens to messages, then adds sender of the message to
    the group chat table if they do not exist.

    This is needed b/c the system requires data about the members in a group chat
    in order to reference them.
    :param update:
    :param context:
    :return:
    """
    user_who_sent_the_message = UserModel(
        telegram_user_id=update.message.from_user.id,
        username=update.message.from_user.username,
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name
    )

    session = get_database()
    try:
        maybe_added_user = await add_user_to_group_chat(session, update.effective_chat, user_who_sent_the_message)
        # TODO: Add message like "The bot has recognized John Doe"
        return
    except NotGroupChatError:
        # await update.message.reply_text("Sorry, you can only create or modify subgroups in group chats.")
        return


async def listen_for_new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_database()

    for member in update.message.new_chat_members:
        new_user = UserModel(
            telegram_user_id=member.id,
            username=member.username,
            first_name=member.first_name,
            last_name=member.last_name)

        maybe_added_user = await add_user_to_group_chat(session, update.effective_chat, new_user)

        if maybe_added_user is not None:
            await update.message.reply_text(f'Welcome {maybe_added_user.username}!')


async def listen_for_left_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_database()
    member = update.message.left_chat_member
    left_user = UserModel(
        telegram_user_id=member.id,
        username=member.username,
        first_name=member.first_name,
        last_name=member.last_name)

    maybe_removed_user = await remove_user_from_group_chat(session, update.effective_chat, left_user)
    if maybe_removed_user is not None:
        await update.message.reply_text(f'Goodbye {maybe_removed_user.username}!')
