import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shout_subgroup.models import Base, UserModel, GroupChatModel

def configure_database() -> bool:
    load_dotenv()

    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_CONTAINER = os.getenv('POSTGRES_CONTAINER')

    try:
        engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_CONTAINER}:5432/{POSTGRES_DB}", echo=True)
    except Exception as ex:
        logging.exception(f"Unable to connect to postgreSQL. See exception details ... {ex}")
        return False

    # Drop the tables during development. Don't use in production
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    global session

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create users
    richie = UserModel(telegram_user_id=12345, username="ashcir", first_name="Richie", last_name="Doe")
    alrick = UserModel(telegram_user_id=67890, username="alrickb", first_name="Alrick", last_name="Rain")
    donovan = UserModel(telegram_user_id=177557021, username=None, first_name="Donovan", last_name="Hail")
    # Going leave it there in case I need it for testing
    # alrick = UserModel(telegram_user_id=67890, username="alrick", first_name="Alrick", last_name="Rain")

    session.add(richie)
    session.add(alrick)
    session.add(donovan)
    session.commit()

    group_chat = GroupChatModel(telegram_group_chat_id=-4239122711, name="Group Chat 1", description="This is a group chat")
    group_chat.users.append(richie)
    group_chat.users.append(alrick)

    session.add(group_chat)
    session.commit()

    return True


def get_database():
    return session