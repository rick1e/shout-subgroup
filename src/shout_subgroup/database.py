from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shout_subgroup.models import Base, UserModel, GroupChatModel

engine = create_engine('sqlite:///pingdem_database.db', echo=True)

# Drop the tables during development. Don't use in production
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Create users
richie = UserModel(telegram_user_id=12345, username="ashcir", first_name="Richie", last_name="Doe")
alrick = UserModel(telegram_user_id=67890, username="alrickb", first_name="Alrick", last_name="Rain")

session.add(richie)
session.add(alrick)
session.commit()

group_chat = GroupChatModel(telegram_group_chat_id=-4239122711, name="Group Chat 1", description="This is a group chat")
group_chat.users.append(richie)
group_chat.users.append(alrick)

session.add(group_chat)
session.commit()
