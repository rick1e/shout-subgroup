import logging

from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes

from shout_subgroup.exceptions import NotGroupChatError
from shout_subgroup.database import session
from shout_subgroup.models import UserModel
from shout_subgroup.repository import (
    find_all_users_in_group_chat,
    find_all_subgroups_in_group_chat,
    find_users_by_usernames,
    find_group_chat_by_telegram_group_chat_id,
    insert_user,
    insert_group_chat
)
from shout_subgroup.utils import is_group_chat
from shout_subgroup.modify_subgroup import remove_users_from_existing_subgroup


async def add_user_to_group_chat(db: Session, chat: Chat, current_user: UserModel) -> UserModel | None:

    if not await is_group_chat(chat.id):
        msg = f"Can't add user to group because telegram chat id {chat.id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)

    if not group_chat:
        group_chat = await insert_group_chat(db, chat.id, chat.title, chat.description)

    all_users = await find_all_users_in_group_chat(db, chat.id)

    # Telegram usernames are case-insensitive,
    # but we're lowercasing these for consistency in string comparisons
    usernames_in_group_chat = [user.username.lower() for user in all_users]
    if current_user.username.lower() not in usernames_in_group_chat:
        added_user = await insert_user(db, current_user.user_id, current_user.username, current_user.first_name, current_user.last_name)
        group_chat.users.append(added_user)
        db.add(group_chat)
        db.commit()
        db.refresh(added_user)
        return added_user

    return None

async def remove_user_from_group_chat(db: Session, chat: Chat, current_user: UserModel) -> UserModel | None:
    if not await is_group_chat(chat.id):
        msg = f"Can't remove user from chat because telegram chat id {chat.id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)
    
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, chat.id)

    if not group_chat:
        return None

    users_to_be_removed = await find_users_by_usernames(db, set([current_user.username]))

    if len(users_to_be_removed) == 1:
        # Remove user from all sub groups as well
        await remove_user_from_all_group_chat_sub_groups(db,chat.id,users_to_be_removed[0])
        group_chat.users.remove(users_to_be_removed[0])
        db.commit()
        db.refresh(group_chat)
        return users_to_be_removed[0]

    return None

async def remove_user_from_all_group_chat_sub_groups(db: Session, telegram_group_chat_id: int, user: UserModel) -> None:

    subgroups = await find_all_subgroups_in_group_chat(db, telegram_group_chat_id)
    for subgroup in subgroups:
        await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup.name, set([user.username]))

async def listen_for_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_user = UserModel(
        telegram_user_id=update.message.from_user.id,
        username=update.message.from_user.username,
        first_name=update.message.from_user.first_name,
        last_name=update.message.from_user.last_name)

    try :
        maybe_added_user = await add_user_to_group_chat(session, update.effective_chat, current_user)
        # TODO: Add message like "The bot has recognized John Doe"
        return
    except NotGroupChatError:
        # await update.message.reply_text("Sorry, you can only create or modify subgroups in group chats.")
        return

async def listen_for_new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for member in update.message.new_chat_members:
        new_user = UserModel(
        telegram_user_id=member.id,
        username=member.username,
        first_name=member.first_name,
        last_name=member.last_name)

        maybe_added_user = await add_user_to_group_chat(session, update.effective_chat, new_user)
        # add_user(member.id, member.username)
        if maybe_added_user is not None:
            await update.message.reply_text(f'Welcome {maybe_added_user.username}!')

async def listen_for_left_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    member = update.message.left_chat_member
    left_user = UserModel(
        telegram_user_id=member.id,
        username=member.username,
        first_name=member.first_name,
        last_name=member.last_name)
    # remove_user(member.id)
    maybe_removed_user = await remove_user_from_group_chat(session,update.effective_chat,left_user)
    if maybe_removed_user is not None:
        await update.message.reply_text(f'Goodbye {maybe_removed_user.username}!')