from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Needed for the many-to-many relationship between
# Users and Subgroups
users_subgroups_join_table = Table(
    'users_subgroups_join_table', Base.metadata,
    Column('subgroup_id', String, ForeignKey('subgroups.subgroup_id')),
    Column('user_id', String, ForeignKey('users.user_id'))
)

# Needed for the many-to-many relationship between
# Users and GroupChats
users_group_chats_join_table = Table(
    'users_group_chats_join_table', Base.metadata,
    Column('group_chat_id', String, ForeignKey('group_chats.group_chat_id')),
    Column('user_id', String, ForeignKey('users.user_id'))
)


class UserModel(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    telegram_user_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class SubgroupModel(Base):
    __tablename__ = 'subgroups'
    subgroup_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    group_chat_id = Column(String, ForeignKey('group_chats.group_chat_id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime)
    users = relationship("UserModel", secondary=users_subgroups_join_table, backref="subgroups")
    table_args = (UniqueConstraint('group_chat_id', 'name', name='_group_chat_id_name_uc'))


class GroupChatModel(Base):
    __tablename__ = 'group_chats'
    group_chat_id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    telegram_group_chat_id = Column(BigInteger, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime)
    subgroups = relationship("SubgroupModel", backref="group_chat")
    users = relationship("UserModel", secondary=users_group_chats_join_table, backref="group_chats")
