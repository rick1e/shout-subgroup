import logging

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from shout_subgroup.database import session
from shout_subgroup.exceptions import NotGroupChatError, SubGroupDoesNotExistsError, UserDoesNotExistsError
from shout_subgroup.models import SubgroupModel
from shout_subgroup.repository import (
    find_subgroup_by_telegram_group_chat_id_and_subgroup_name,
    remove_users_from_subgroup
)
from shout_subgroup.utils import is_group_chat, replace_me_mentions, are_mentions_valid, UserIdMentionMapping, \
    get_user_id_from_mention


async def remove_subgroup_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles removing members from subgroups.
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
        msg = "You didn't use this command correctly. Please type /kick <group_name> @alice @bob ... @zack"
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

        user_ids: set[str | None] = {id_and_mention.user_id for id_and_mention in users_ids_and_mentions}
        subgroup = await remove_users_from_existing_subgroup(
            session,
            update.effective_chat.id,
            subgroup_name,
            user_ids
        )

        subgroup_usernames = [f"@{user.username}" for user in subgroup.users]
        joined_usernames = ", ".join(subgroup_usernames)
        msg = (
            f"Subgroup {subgroup.name} now has the following members {joined_usernames}"
            if subgroup.users
            else f"Subgroup '{subgroup.name}' has no members"
        )
        await update.message.reply_text(msg)
        return

    except NotGroupChatError:
        await update.message.reply_text("Sorry, you can only create or modify subgroups in group chats.")
        return

    except SubGroupDoesNotExistsError:
        msg = f"I can't kick members because subgroup '{subgroup_name}' does not exist"
        await update.message.reply_text(msg)

    except UserDoesNotExistsError:
        msg = (f"We don't have a record for some of the users. "
               f"We can only remove users we know about. "
               f"Please tell some or all the users to send a message to this chat.")
        await update.message.reply_text(msg)

    except Exception:
        logging.exception("An unexpected exception occurred")
        await update.message.reply_text("Whoops 😅, something went wrong on our side.")


async def remove_users_from_existing_subgroup(
        db: Session,
        telegram_chat_id: int,
        subgroup_name: str,
        user_ids: set[int | None]
) -> SubgroupModel:
    if not await is_group_chat(telegram_chat_id):
        msg = f"Can't kick members from subgroup because telegram chat id {telegram_chat_id} is not a group chat."
        logging.info(msg)
        raise NotGroupChatError(msg)

    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_chat_id, subgroup_name)
    if not subgroup:
        msg = f"Subgroup {subgroup_name} should exist for telegram group chat id {telegram_chat_id}."
        logging.info(msg)
        raise SubGroupDoesNotExistsError(msg)

    if None in user_ids:
        # If we can't find all the users, then it means we have not
        # saved them yet. The user would have to type a message for the
        # bot to see.
        raise UserDoesNotExistsError("All the usernames are not in the database.")

    await remove_users_from_subgroup(db, subgroup, user_ids)

    return subgroup
