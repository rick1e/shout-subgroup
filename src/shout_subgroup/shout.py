from dataclasses import dataclass, asdict

@dataclass
class User:
    """Stores users information"""
    id: int
    username: str
    first_name: str
    
def mention_user(user: User) -> str:
    mention = ""
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"[{user.first_name}](tg://user?id={user.id})"

    return mention

def create_message_to_mention_members(members) -> str:
    message = ""
    for member_key in members:
        message += mention_user(members[member_key])+" "

    return message