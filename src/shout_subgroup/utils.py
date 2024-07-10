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
