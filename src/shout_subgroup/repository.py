from typing import Sequence

from telegram import Chat
from sqlalchemy import select
from sqlalchemy.orm import Session

from shout_subgroup.database import session
from shout_subgroup.models import SubgroupModel, UserModel, GroupChatModel, users_group_chats_join_table

async def find_all_users_in_GC(db: Session, telegram_group_chat_id:int) -> Sequence[UserModel]:
    
    users = db.query(UserModel).join(users_group_chats_join_table).join(GroupChatModel).filter(
        GroupChatModel.telegram_group_chat_id == telegram_group_chat_id
    ).all()
    
    return users

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
