from dataclasses import dataclass, asdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Sequence
from shout_subgroup.models import UserModel, users_group_chats_join_table, GroupChatModel

async def shout_all_members(db: Session, telegram_group_chat_id:int) -> str:
    
    all_members = await find_all_users_in_GC(db, telegram_group_chat_id)
    message = create_message_to_mention_members(all_members)
    return message
    
def mention_user(user: UserModel) -> str:
    mention = ""
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"[{user.first_name}](tg://user?id={user.telegram_user_id})"

    return mention

def create_message_to_mention_members(members: Sequence[UserModel]) -> str:
    message = ""
    for member in members:
        message += mention_user(member)+" "

    return message

async def find_all_users_in_GC(db: Session, telegram_group_chat_id:int) -> Sequence[UserModel]:
    
    users = db.query(UserModel).join(users_group_chats_join_table).join(GroupChatModel).filter(
        GroupChatModel.telegram_group_chat_id == telegram_group_chat_id
    ).all()
    
    return users