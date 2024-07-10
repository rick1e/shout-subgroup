from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shout_subgroup.models import Base, UserModel, GroupChatModel
from shout_subgroup.create_subgroup import create_subgroup

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
    john = UserModel(telegram_user_id=12345, username="@johndoe", first_name="John", last_name="Doe")
    jane = UserModel(telegram_user_id=67890, username="@janedoe", first_name="Jane", last_name="Doe")
    group_chat = GroupChatModel(
        telegram_group_chat_id=TELEGRAM_GROUP_CHAT_ID,
        name=TELEGRAM_GROUP_CHAT_NAME,
        description=TELEGRAM_GROUP_CHAT_DESCRIPTION
    )
    session.add(john)
    session.add(jane)
    session.add(group_chat)
    session.commit()

    yield session

    # Close the session and drop all tables
    session.close()
    Base.metadata.drop_all(bind=engine)


class MockTelegramChat:
    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description


@pytest.mark.asyncio
async def test_create_subgroup(session: Session):
    # Given: A group chat already exists
    # The database is seeded with one

    # And: We have the subgroup information
    telegram_chat = Mock()
    telegram_chat.id = TELEGRAM_GROUP_CHAT_ID
    telegram_chat.title = TELEGRAM_GROUP_CHAT_NAME
    telegram_chat.description = TELEGRAM_GROUP_CHAT_DESCRIPTION

    subgroup_name = "Archery"
    usernames = {"@johndoe", "@janedoe"}

    # When: We add subgroup
    subgroup = await create_subgroup(session, telegram_chat, subgroup_name, usernames)

    # Then: It's added correctly
    assert subgroup.subgroup_id is not None
    assert subgroup.name == subgroup_name
    assert subgroup.group_chat_id is not None

    assert len(subgroup.users) == 2
    assert set([user.username for user in subgroup.users]) == usernames

