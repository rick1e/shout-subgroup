import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.shout_subgroup.models import Base, UserModel, GroupChatModel

# Create an SQLite in-memory database and a session factory
engine = create_engine('sqlite:///:memory:', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed the database with initial data
    session = SessionLocal()
    user1 = UserModel(telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    user2 = UserModel(telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    group_chat = GroupChatModel(
        telegram_group_chat_id=-123456789,
        name="Example Group Chat",
        description="This is an example group chat"
    )
    session.add(user1)
    session.add(user2)
    session.add(group_chat)
    session.commit()

    yield session

    # Close the session and drop all tables
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_create_subgroup(session: Session):
    print(session)
    assert True
