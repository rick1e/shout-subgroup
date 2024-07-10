# Initialize the file-based SQLite database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shout_subgroup.models import Base, UserModel, SubgroupModel, GroupChatModel

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
#
# # Create a subgroup and associate users
# subgroup = SubgroupModel(name="Subgroup 1", description="This is the first subgroup", users=[user1, user2])
#
# # Create a group chat and associate the subgroup
group_chat = GroupChatModel(telegram_group_chat_id=-4239122711, name="Group Chat 1", description="This is a group chat")

group_chat.users.append(richie)
group_chat.users.append(alrick)

#
# # Persist data to the database
session.add(group_chat)
session.commit()
