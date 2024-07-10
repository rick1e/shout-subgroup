from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from shout_subgroup.models import Base, UserModel, GroupChatModel
from shout_subgroup.shout import shout_all_members

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
async def test_shout_all_members(session: Session):
    # Given: A group chat already exists
    # The database is seeded with one with users

    usernames = {"@johndoe", "@janedoe"}

    # When: We add subgroup
    message = await shout_all_members(session)

    # Then: It's added correctly
    assert message == "@johndoe @janedoe "

