def usernames_valid(usernames: set[str]) -> bool:
    """
    Checks if usernames are valid strings
    :param usernames:
    :return: True if valid
    """
    # TODO: Implement stricter validations later
    return all(isinstance(item, str) for item in usernames)
