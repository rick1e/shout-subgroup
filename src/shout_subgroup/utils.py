import re

from sqlalchemy.orm import Session
from telegram import User

from shout_subgroup.repository import find_user_by_username, find_user_by_telegram_user_id


async def usernames_valid(usernames: set[str]) -> bool:
    """
    Checks if usernames are valid strings
    :param usernames:
    :return: True if valid
    """
    # TODO: Implement stricter validations later
    return all(isinstance(item, str) for item in usernames)


async def is_group_chat(telegram_chat_id: int) -> bool:
    """
    Returns True if the telegram chat id is from a group chat
    :param telegram_chat_id:
    :return: True if from group chat
    """
    # Telegram uses negative numbers for group chats
    # If it's a positive number, that means it's an individual.
    # We can't create subgroup for an individual.
    return telegram_chat_id <= 0


async def format_telegram_usernames(usernames: set[str], telegram_user: User) -> set[str]:
    """
    Takes the Telegram usernames then converts them
    into a format we save within our system.
    We don't save the '@' symbol, and we also convert "@me"
    into the corresponding username.
    :param usernames:
    :param telegram_user:
    :return: set
    """

    # Removing the '@' mention from args for usernames
    formatted_usernames = {name.replace("@", "") for name in usernames}

    # Check if any of the usernames is "@me".
    # If it's "@me", we're going to treat is as an alias
    # for the user who sent the message b/c when you type '@' in
    # Telegram it does not show yourself as an option.
    aliased_usernames = {
        _replace_me_mention_with_username(name, telegram_user)
        for name in formatted_usernames
    }

    return aliased_usernames


def _replace_me_mention_with_username(username: str, telegram_user: User) -> str:
    # TODO: Update logic when we decide how to handle Users without usernames
    return telegram_user.username.lower() if username.lower() == "me" else username


async def get_user_id_from_mention(db: Session, username_or_markdown: str) -> int | None:
    if username_or_markdown[0] == "@":
        return await _convert_username_to_user_id(db, username_or_markdown)

    return await _convert_markdown_to_user_id(db, username_or_markdown)


async def _convert_username_to_user_id(db: Session, telegram_username: str) -> int | None:
    """
    Converts from a telegram username to our user id
    :param db:
    :param telegram_username:
    :return: the user id used within our system. None if user doesn't exist
    """
    user = await find_user_by_username(db, telegram_username)
    if not user:
        return None

    return user.user_id


async def _convert_markdown_to_user_id(db: Session, telegram_markdown_v2: str) -> int | None:
    """
    Convert from telegram markdown into our user id.
    E.g. [John](tg://user?id=12345678)
    :param db:
    :param telegram_markdown_v2:
    :return: the user id used within our system
    """

    # Regular expression to match the first name and user ID
    pattern = r'\[(?P<firstname>[^\]]+)\]\(tg://user\?id=(?P<telegram_user_id>\d+)\)'

    match = re.search(pattern, telegram_markdown_v2)
    if not match:
        return None

    telegram_user_id = match.group('telegram_user_id')
    user = await find_user_by_telegram_user_id(db, telegram_user_id)

    if not user:
        return None

    return user.user_id
