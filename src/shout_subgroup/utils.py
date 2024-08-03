from telegram import User


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
