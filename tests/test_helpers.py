from sqlalchemy.orm import Session

from shout_subgroup.models import GroupChatModel, SubgroupModel, UserModel


def create_test_user(session: Session, telegram_user_id, username, first_name, last_name) -> UserModel:
    user = UserModel(
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def create_test_subgroup(
        session: Session,
        group_chat_id: str,
        name: str,
        users: list[UserModel],
) -> SubgroupModel:
    subgroup = SubgroupModel(
        group_chat_id=group_chat_id,
        name=name
    )

    for user in users:
        subgroup.users.append(user)

    session.add(subgroup)
    session.commit()
    session.refresh(subgroup)
    return subgroup


def create_test_group_chat(
        session: Session,
        telegram_group_chat_id: int,
        name: str,
        users: list[UserModel],
        description: str = "This is an example group chat"
) -> GroupChatModel:
    group_chat = GroupChatModel(
        telegram_group_chat_id=telegram_group_chat_id,
        name=name,
        description=description
    )

    for user in users:
        group_chat.users.append(user)

    session.add(group_chat)
    session.commit()
    session.refresh(group_chat)

    return group_chat
