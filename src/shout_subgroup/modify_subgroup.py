import logging

from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.exceptions import NotGroupChatError, SubGroupExistsError, UserDoesNotExistsError
from shout_subgroup.models import SubgroupModel
from shout_subgroup.repository import (find_subgroup_by_telegram_group_chat_id_and_subgroup_name,
                                       find_group_chat_by_telegram_group_chat_id, find_users_by_usernames,
                                       insert_subgroup,
                                       insert_group_chat)
from shout_subgroup.utils import usernames_valid, is_group_chat


async def create_subgroup(db: Session,
                          telegram_chat: Chat,
                          subgroup_name: str,
                          usernames: set[str]) -> SubgroupModel:
    telegram_chat_id = telegram_chat.id
    if not await is_group_chat(telegram_chat_id):
        msg = f"Can't create subgroup because telegram chat id {telegram_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    # If the code reaches to this point the telegram_chat_id has to be a telegram group chat id
    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_chat_id, subgroup_name)
    if subgroup:
        msg = f"Subgroup {subgroup_name} already exists for telegram group chat id {telegram_chat_id}."
        logging.info(msg)
        raise SubGroupExistsError(msg)

    users_to_be_added = await find_users_by_usernames(db, usernames)
    # If we can't find all the users, then it means we have not
    # saved them yet. The user would have to type a message for the
    # bot to see.
    if len(users_to_be_added) != len(usernames):
        raise UserDoesNotExistsError("All the usernames are not in the database.")

    # Business logic
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, telegram_chat_id)
    # If the group chat doesn't exist in our system yet, we'll have to create it.
    if not group_chat:
        created_group_chat = await insert_group_chat(db, telegram_chat)
        created_subgroup = await insert_subgroup(db, subgroup_name, created_group_chat.group_chat_id, users_to_be_added)
        return created_subgroup

    created_subgroup = await insert_subgroup(db, subgroup_name, group_chat.group_chat_id, users_to_be_added)
    return created_subgroup


async def does_subgroup_exist(db: Session, telegram_group_chat_id: int, subgroup_name: str) -> bool:

    # TODO: Add test
    if not await is_group_chat(telegram_group_chat_id):
        msg = f"Can't list subgroups because telegram chat id {telegram_group_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(
        db,
        telegram_group_chat_id,
        subgroup_name
    )

    return subgroup is not None


async def subgroup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the create subgroup command.
    This function should not handle business logic,
    or storing data. It will delegate that responsibility
    to other functions. Similar to controllers from the MVC pattern.
    :param update:
    :param context:
    :return:
    """

    args = context.args

    # Quick guard clause
    if len(args) < 2:
        msg = "You didn't use this command correctly. Please type /group <group_name> @alice @bob ... @zack"
        await update.message.reply_text(msg)
        return

    chat_id = update.effective_chat.id
    subgroup_name = args[0]

    usernames = {name.replace("@", "") for name in set(args[1:])}  # removing mention from args for usernames
    if not await usernames_valid(usernames):
        await update.message.reply_text("Not all the usernames are valid. Please re-check what you entered.")

    try:

        is_existing_subgroup = await does_subgroup_exist(session, chat_id, subgroup_name)
        if is_existing_subgroup:
            # TODO: implement service logic
            await update.message.reply_text(f"Mock reply when subgroup {subgroup_name} already exists")
            return
        else:
            subgroup = await create_subgroup(session, update.effective_chat, subgroup_name, usernames)
            subgroup_usernames = [user.username for user in subgroup.users]
            await update.message.reply_text(f"Subgroup {subgroup.name} was created with users {subgroup_usernames}")
            return

    except NotGroupChatError:
        await update.message.reply_text("Sorry, you can only create or modify subgroups in group chats.")
        return

    except SubGroupExistsError:
        await update.message.reply_text(
            f'"{subgroup_name}" group already exists. Remove the group if you want to recreate it'
        )

    except UserDoesNotExistsError:
        msg = (f"We don't have a record for some of the users. "
               f"We can only add users we know about. "
               f"Please tell some or all the users to send a message to this chat.")
        await update.message.reply_text(msg)

    except Exception:
        logging.exception("An unexpected exception occurred")
        await update.message.reply_text("Whoops 😅, something went wrong on our side.")
