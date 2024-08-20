import logging

from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes

from shout_subgroup.exceptions import (
    NotGroupChatError,
    SubGroupExistsError,
    UserDoesNotExistsError,
    SubGroupDoesNotExistsError
)
from shout_subgroup.models import SubgroupModel
from shout_subgroup.repository import (find_subgroup_by_telegram_group_chat_id_and_subgroup_name,
                                       find_group_chat_by_telegram_group_chat_id, insert_subgroup,
                                       insert_group_chat, find_users_by_user_ids, add_users_to_subgroup)
from shout_subgroup.utils import (
    are_mentions_valid,
    is_group_chat,
    replace_me_mentions,
    get_user_id_from_mention,
    UserIdMentionMapping,
    get_mention_from_user_id_mention_mappings,
    create_mention_from_user_id
)

from shout_subgroup.database import get_database


async def _handle_create_subgroup(
        db: Session,
        update: Update,
        subgroup_name: str,
        users_ids_and_mentions: set[UserIdMentionMapping]
):
    user_ids: set[str | None] = {id_and_mention.user_id for id_and_mention in users_ids_and_mentions}
    subgroup = await create_subgroup(db, update.effective_chat, subgroup_name, user_ids)

    # Note: This list shouldn't have a None value
    # b/c we'd have thrown a UserDoesNotExistsError during create_subgroup
    subgroup_mentions: list[str | None] = [
        await get_mention_from_user_id_mention_mappings(user.user_id, users_ids_and_mentions)
        for user in subgroup.users
    ]
    joined_usernames = ", ".join(subgroup_mentions)
    await update.message.reply_text(
        f"Subgroup {subgroup.name} was created with users {joined_usernames}",
        parse_mode="markdown"
    )
    return


async def create_subgroup(
        db: Session,
        telegram_chat: Chat,
        subgroup_name: str,
        user_ids: set[int | None]
) -> SubgroupModel:
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

    if None in user_ids:
        # If we can't find all the users, then it means we have not
        # saved them yet. The user would have to type a message for the
        # bot to see.
        raise UserDoesNotExistsError("All the usernames are not in the database.")

    users_to_be_added = await find_users_by_user_ids(db, user_ids)

    # Business logic
    group_chat = await find_group_chat_by_telegram_group_chat_id(db, telegram_chat_id)
    # If the group chat doesn't exist in our system yet, we'll have to create it.
    if not group_chat:
        created_group_chat = await insert_group_chat(
            db,
            telegram_chat.id,
            telegram_chat.title,
            telegram_chat.description
        )

        created_subgroup = await insert_subgroup(db, subgroup_name, created_group_chat.group_chat_id, users_to_be_added)
        return created_subgroup

    created_subgroup = await insert_subgroup(db, subgroup_name, group_chat.group_chat_id, users_to_be_added)
    return created_subgroup


async def _handle_add_users_to_existing_subgroup(
        db: Session,
        update: Update,
        subgroup_name: str,
        users_ids_and_mentions: set[UserIdMentionMapping]
) -> None:
    user_ids: set[str | None] = {id_and_mention.user_id for id_and_mention in users_ids_and_mentions}
    subgroup: SubgroupModel = await add_users_to_existing_subgroup(
        db,
        update.effective_chat.id,
        subgroup_name,
        user_ids
    )
    # Note: This list shouldn't have a None value
    # b/c we'd have thrown a UserDoesNotExistsError during create_subgroup
    subgroup_mentions: list[str | None] = [
        await create_mention_from_user_id(db, user.user_id)
        for user in subgroup.users
    ]
    joined_usernames = ", ".join(subgroup_mentions)
    await update.message.reply_text(
        f"Subgroup '{subgroup.name}' now has the following members {joined_usernames}",
        parse_mode="markdown"
    )
    return


async def add_users_to_existing_subgroup(
        db: Session,
        telegram_chat_id: int,
        subgroup_name: str,
        user_ids: set[int | None]
) -> SubgroupModel:
    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_chat_id, subgroup_name)
    if not subgroup:
        # At this point we should have the subgroup, an error occurred if we hit this code
        msg = f"Subgroup {subgroup_name} should exist for telegram group chat id {telegram_chat_id}."
        logging.exception(msg)
        raise SubGroupDoesNotExistsError(msg)

    if None in user_ids:
        # If we can't find all the users, then it means we have not
        # saved them yet. The user would have to type a message for the
        # bot to see.
        raise UserDoesNotExistsError("All the usernames are not in the database.")

    await add_users_to_subgroup(db, subgroup, user_ids)

    return subgroup


async def does_subgroup_exist(db: Session, telegram_group_chat_id: int, subgroup_name: str) -> bool:
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
    session = get_database()

    # Quick guard clause
    if len(args) < 2:
        msg = "You didn't use this command correctly. Please type /group <group_name> @alice @bob ... @zack"
        await update.message.reply_text(msg)
        return

    subgroup_name = args[0]

    # The text markdown contains the username if it exists.
    # When a user doesn't have a username, telegram uses an url
    # [John](tg://user?id=12345678). We'll pull the user_id
    # either from the username or the URL
    user_mentions = set(update.effective_message.text_markdown_v2.split()[2:])
    formatted_user_mentions = await replace_me_mentions(user_mentions, update.effective_user)

    if not await are_mentions_valid(formatted_user_mentions):
        await update.message.reply_text("Not all the usernames are valid. Please re-check what you entered.")

    users_ids_and_mentions: set[UserIdMentionMapping] = {
        await get_user_id_from_mention(session, mention)
        for mention in formatted_user_mentions
    }

    try:

        is_existing_subgroup = await does_subgroup_exist(session, update.effective_chat.id, subgroup_name)
        if is_existing_subgroup:
            await _handle_add_users_to_existing_subgroup(session, update, subgroup_name, users_ids_and_mentions)
            return
        else:
            await _handle_create_subgroup(session, update, subgroup_name, users_ids_and_mentions)
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

    except SubGroupDoesNotExistsError:
        msg = f"Whoops 🧐, we couldn't find subgroup {subgroup_name}. Something went wrong on our side."
        await update.message.reply_text(msg)

    except Exception:
        logging.exception("An unexpected exception occurred")
        await update.message.reply_text("Whoops 😅, something went wrong on our side.")


