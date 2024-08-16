import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session
from telegram import User

from shout_subgroup.exceptions import UserDoesNotExistsError
from shout_subgroup.repository import find_user_by_username, find_user_by_telegram_user_id, find_user_by_user_id


async def are_mentions_valid(usernames: set[str]) -> bool:
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


async def replace_me_mentions(usernames: set[str], telegram_user: User) -> set[str]:
    """
    Converts "@me" into the corresponding username.
    :param usernames:
    :param telegram_user:
    :return: set
    """

    # Check if any of the usernames is "@me".
    # If it's "@me", we're going to treat is as an alias
    # for the user who sent the message b/c when you type '@' in
    # Telegram it does not show yourself as an option.
    aliased_usernames = {
        _replace_me_mention_with_username(name, telegram_user)
        for name in usernames
    }

    return aliased_usernames


def _replace_me_mention_with_username(username: str, telegram_user: User) -> str:
    return telegram_user.name.lower() if username.lower() == "@me" else username


@dataclass(frozen=True, eq=True)
class UserIdMentionMapping:
    """
    Convenient class for tying user ids to the mentions
    """
    mention: str
    user_id: str | None


async def get_user_id_from_mention(db: Session, username_or_markdown: str) -> UserIdMentionMapping:
    user_id = (
        await _convert_username_to_user_id(db, username_or_markdown[1:].lower())
        if username_or_markdown[0] == "@"
        else await _convert_markdown_to_user_id(db, username_or_markdown)
    )

    return UserIdMentionMapping(user_id=user_id, mention=username_or_markdown)


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


async def get_mention_from_user_id_mention_mappings(
        user_id: str,
        users_ids_and_mentions: set[UserIdMentionMapping]) -> str | None:
    """
    Find the UserIdMention mapping for a given user id
    :param user_id:
    :param users_ids_and_mentions:
    :return: the mapping if found, None if not
    """

    for mapping in users_ids_and_mentions:
        if mapping.user_id == user_id:
            return mapping.mention

    return None


async def create_mention_from_user_id(db: Session, user_id: str) -> str:
    """
    Creates the mention reply text for a user id
    :param db:
    :param user_id:
    :return:
    """
    user = await find_user_by_user_id(db, user_id)

    if not user:
        msg = f"Can not create mention for user id {user_id} because it does not exist"
        logging.info(msg)
        raise UserDoesNotExistsError(msg)

    # If the user has a username, we can mention
    # them with it. Otherwise, we have to generate
    # markdown that Telegram recognizes
    if user.username:
        return f"@{user.username}"

    # [John](tg://user?id=12345678)
    return f"[{user.first_name}](tg://user?id={user.telegram_user_id})"
