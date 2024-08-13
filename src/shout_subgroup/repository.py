from typing import Sequence, Type

from sqlalchemy import select
from sqlalchemy.orm import Session
from telegram import Chat

from shout_subgroup.models import SubgroupModel, UserModel, GroupChatModel, users_group_chats_join_table, \
    users_subgroups_join_table


async def find_all_users_in_subgroup(db: Session, group_chat_id: int, subgroup_name: str) -> list[Type[UserModel]]:
    users = (
        db.query(UserModel)
        .join(users_subgroups_join_table)
        .join(SubgroupModel)
        .filter(SubgroupModel.name == subgroup_name, SubgroupModel.group_chat_id == group_chat_id)
        .all()
    )

    return users


async def find_all_users_in_group_chat(db: Session, telegram_group_chat_id: int) -> list[Type[UserModel]]:
    users = (
        db.query(UserModel)
        .join(users_group_chats_join_table)
        .join(GroupChatModel)
        .filter(GroupChatModel.telegram_group_chat_id == telegram_group_chat_id)
        .all()
    )

    return users


async def find_all_subgroups_in_group_chat(db: Session, telegram_group_chat_id: int) -> list[Type[SubgroupModel]]:
    """
    Finds all subgroups for a group chat
    :param db: SQLAlchemy session
    :param telegram_group_chat_id:
    :return: the list of subgroups
    """
    result = (
        db.query(SubgroupModel)
        .join(GroupChatModel)
        .filter(GroupChatModel.telegram_group_chat_id == telegram_group_chat_id)
        .all()
    )

    return result


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


async def find_users_by_user_ids(db: Session, user_ids: set[int]) -> Sequence[UserModel]:
    stmt = (
        select(UserModel)
        .where(UserModel.user_id.in_(user_ids))
    )
    result = db.execute(stmt).scalars().all()
    return result


async def find_user_by_user_id(db: Session, user_id: str) -> UserModel | None:
    stmt = (
        select(UserModel)
        .where(UserModel.user_id == user_id)
    )
    result = db.execute(stmt).scalars().first()
    return result


async def find_user_by_username(db: Session, username: str) -> UserModel | None:
    stmt = (
        select(UserModel)
        .where(UserModel.username == username)
    )
    result = db.execute(stmt).scalars().first()
    return result


async def find_user_by_telegram_user_id(db: Session, telegram_user_id: int) -> UserModel | None:
    stmt = (
        select(UserModel)
        .where(UserModel.telegram_user_id == telegram_user_id)
    )
    result = db.execute(stmt).scalars().first()
    return result


async def find_group_chat_by_telegram_group_chat_id(db: Session, telegram_group_chat_id: int) -> GroupChatModel | None:
    stmt = (
        select(GroupChatModel)
        .where(GroupChatModel.telegram_group_chat_id == telegram_group_chat_id)
    )

    result = db.execute(stmt).scalars().first()
    return result

async def insert_user(
        db: Session,
        user_id: int,
        username: str,
        first_name: str,
        last_name: str
) -> UserModel:
    new_user = UserModel(
        telegram_user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


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


async def delete_subgroup(
        db: Session,
        telegram_group_chat_id: int,
        subgroup_name: str,
) -> bool:
    """
    Hard deletes a subgroup from the database.
    This delete is a cascading delete, meaning
    if there are users associated with the subgroup,
    the associations will be removed prior to the deletion.
    :param db:
    :param telegram_group_chat_id:
    :param subgroup_name:
    :return:
    """

    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(
        db,
        telegram_group_chat_id,
        subgroup_name
    )

    if not subgroup:
        return False

    # This is a cascading delete.
    # We'll remove the users in the subgroup prior to deletion
    subgroup.users.clear()
    db.commit()

    # Delete the subgroup
    db.delete(subgroup)
    db.commit()

    return True


async def insert_group_chat(db: Session,
                            telegram_chat_id: int,
                            telegram_chat_title: str,
                            telegram_chat_description: str
                            ) -> GroupChatModel:
    new_group_chat = GroupChatModel(
        telegram_group_chat_id=telegram_chat_id,
        name=telegram_chat_title,
        description=telegram_chat_description
    )

    db.add(new_group_chat)
    db.commit()
    db.refresh(new_group_chat)  # Refresh to get the ID and other generated values
    return new_group_chat
