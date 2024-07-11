import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shout_subgroup.exceptions import NotGroupChatError
from shout_subgroup.list_subgroup import list_subgroups
from shout_subgroup.models import Base, UserModel, GroupChatModel, SubgroupModel

TELEGRAM_GROUP_CHAT_DESCRIPTION = "This is an example group chat"
TELEGRAM_GROUP_CHAT_NAME = "Example Group Chat"
TELEGRAM_GROUP_CHAT_ID = -123456789

# Create an SQLite in-memory database and a session factory
engine = create_engine('sqlite:///:memory:', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed the database with initial data
    session = SessionLocal()
    john = UserModel(telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = UserModel(telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    group_chat = GroupChatModel(
        telegram_group_chat_id=TELEGRAM_GROUP_CHAT_ID,
        name=TELEGRAM_GROUP_CHAT_NAME,
        description=TELEGRAM_GROUP_CHAT_DESCRIPTION
    )
    session.add(john)
    session.add(jane)
    group_chat.users.append(john)
    group_chat.users.append(jane)
    session.add(group_chat)
    session.commit()

    yield session

    # Close the session and drop all tables
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_list_subgroup(session: Session):
    # Given: A subgroup exists in the group chat
    telegram_group_chat_id = -123
    subgroup_names = ["mock-subgroup-1", "mock-subgroup-2", "mock-subgroup-3"]
    await create_test_group_chat_with_subgroups(session, telegram_group_chat_id, subgroup_names)

    # When: We list the subgroups
    result = await list_subgroups(session, telegram_group_chat_id)

    # Then: All of them should appear
    assert len(result) == len(subgroup_names)
    result_names = [sub.name for sub in result]
    assert set(result_names) == set(subgroup_names)


@pytest.mark.asyncio
async def test_list_subgroup_for_no_subgroups(session: Session):
    # Given: No subgroups exits in the group chat
    telegram_group_chat_id = -123
    subgroup_names = []
    await create_test_group_chat_with_subgroups(session, telegram_group_chat_id, subgroup_names)

    # When: We list the subgroups
    result = await list_subgroups(session, telegram_group_chat_id)

    # Then: An empty string is returned
    assert result == []


@pytest.mark.asyncio
async def test_list_subgroup_throws_not_group_chat_exception(session: Session):
    # Given: The telegram chat is not a group chat
    user_chat_id = 123

    # When: We try to list the subgroups
    # Then: An exception is thrown
    with pytest.raises(NotGroupChatError) as ex:
        await list_subgroups(session, user_chat_id)

    assert str(user_chat_id) in ex.value.message


async def create_test_group_chat_with_subgroups(
        session: Session,
        telegram_group_chat_id: int,
        subgroup_names: list[str]
) -> tuple[GroupChatModel, list[SubgroupModel]]:
    group_chat = GroupChatModel(
        telegram_group_chat_id=telegram_group_chat_id,
        name="Test Group Chat",
        description="A test group chat"
    )
    session.add(group_chat)
    session.commit()

    subgroups = [
        SubgroupModel(name=name, group_chat_id=group_chat.group_chat_id)
        for name in subgroup_names
    ]
    session.add_all(subgroups)
    session.commit()

    return group_chat, subgroups
