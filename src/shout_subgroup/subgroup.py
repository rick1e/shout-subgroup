import logging
import os
from typing import Sequence

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session
from telegram import Update, Chat
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler

from shout_subgroup.database import session
from shout_subgroup.models import SubgroupModel, UserModel, GroupChatModel


class NotGroupChatError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SubGroupExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class UserDoesNotExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


async def create_subgroup(db: Session,
                          telegram_chat: Chat,
                          subgroup_name: str,
                          usernames: set[str]) -> SubgroupModel:
    # Telegram uses negative numbers for group chats
    # If it's a positive number, that means it's an individual.
    # We can't create subgroup for an individual.
    telegram_chat_id = telegram_chat.id
    if telegram_chat_id >= 0:
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


async def insert_subgroup(
        db: Session,
        subgroup_name: str,
        group_chat_id: str,
        users: Sequence[UserModel]
) -> SubgroupModel:
    new_subgroup = SubgroupModel(
        name=subgroup_name,
        group_chat_id=group_chat_id,
        users=users
    )
    db.add(new_subgroup)
    db.commit()
    db.refresh(new_subgroup)
    return new_subgroup


async def find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db: Session,
                                                                    telegram_group_chat_id: int,
                                                                    subgroup_name: str) -> SubgroupModel | None:
    result = (
        db.query(SubgroupModel)
        .join(GroupChatModel)
        .filter(
            GroupChatModel.telegram_group_chat_id == telegram_group_chat_id,
            SubgroupModel.name == subgroup_name
        ).first()
    )

    return result


async def find_users_by_usernames(db: Session, usernames: set[str]) -> Sequence[UserModel]:
    stmt = (
        select(UserModel)
        .where(UserModel.username.in_(usernames))
    )
    result = db.execute(stmt).scalars().all()
    return result


async def find_group_chat_by_telegram_group_chat_id(db: Session, telegram_group_chat_id: int) -> GroupChatModel | None:
    stmt = (
        select(GroupChatModel)
        .where(GroupChatModel.telegram_group_chat_id == telegram_group_chat_id)
    )

    result = db.execute(stmt).scalars().first()
    return result


async def insert_group_chat(db: Session, telegram_chat: Chat) -> GroupChatModel:
    new_group_chat = GroupChatModel(
        telegram_group_chat_id=telegram_chat.id,
        name=telegram_chat.title,
        description=telegram_chat.description if hasattr(telegram_chat, 'description') else ""
    )
    db.add(new_group_chat)
    db.commit()
    db.refresh(new_group_chat)  # Refresh to get the ID and other generated values
    return new_group_chat


def usernames_valid(usernames: set[str]) -> bool:
    """
    Checks if usernames are valid strings
    :param usernames:
    :return: True if valid
    """
    # TODO: Implement stricter validations later
    return all(isinstance(item, str) for item in usernames)


async def create_subgroup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    usernames: set[str] = set(args[1:])  # Using a set here to remove duplicates
    if not usernames_valid(usernames):
        await update.message.reply_text("Not all the usernames are valid. Please re-check what you entered.")

    subgroup_name = args[0]

    try:

        subgroup = await create_subgroup(session, update.effective_chat, subgroup_name, usernames)
        subgroup_usernames = [user.username for user in subgroup.users]
        await update.message.reply_text(f"Subgroup {subgroup.name} was created with users {subgroup_usernames}")
        return

    except NotGroupChatError:
        await update.message.reply_text("Sorry, you can only create subgroups in group chats.")
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


def main() -> None:
    load_dotenv()
    token = os.getenv('TELEGRAM_API_KEY')

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("group", create_subgroup_handler))
    app.run_polling()


if __name__ == '__main__':
    main()
