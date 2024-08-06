from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session
from telegram import Chat

from shout_subgroup.exceptions import SubGroupDoesNotExistsError, UserDoesNotExistsError, NotGroupChatError
from shout_subgroup.group_chat_listener import add_user_to_group_chat
from shout_subgroup.models import UserModel
from shout_subgroup.modify_subgroup import add_users_to_existing_subgroup, remove_users_from_existing_subgroup
from shout_subgroup.repository import find_group_chat_by_telegram_group_chat_id
from test_helpers import create_test_user, create_test_group_chat, create_test_subgroup


class MockTelegramChat:
    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description


@pytest.mark.asyncio
async def test_add_user_if_not_in_group_chat(db: Session):
    # Given: A group chat exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_group_chat_description = "Test Chatting"

    initial_group_chat_users = [john, jane]
    group_chat = create_test_group_chat(db, telegram_group_chat_id, telegram_group_chat_name, initial_group_chat_users)

    # But: The user is not in the group chat
    betty = Mock()
    betty.id = 87654
    betty.username = "betty"
    betty.first_name = "Betty"
    betty.last_name = "White"

    telegram_chat = Mock()
    telegram_chat.id = telegram_group_chat_id
    telegram_chat.title = telegram_group_chat_name
    telegram_chat.description = telegram_group_chat_description

    # When: The listener determines this
    added_user = await add_user_to_group_chat(db, telegram_chat, betty)

    # Then: The user should be added to the group chat
    assert len(group_chat.users) == 3

    assert added_user.user_id is not None

    actual_user = next((user for user in group_chat.users if user.username == betty.username), None)
    assert actual_user.first_name == added_user.first_name
    assert actual_user.last_name == added_user.last_name
    assert actual_user.telegram_user_id == added_user.telegram_user_id


@pytest.mark.asyncio
async def test_ignore_user_if_already_in_group_chat(db: Session):
    # Given: A group chat exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_group_chat_description = "Test Chatting"

    initial_group_chat_users = [john, jane]
    group_chat = create_test_group_chat(db, telegram_group_chat_id, telegram_group_chat_name, initial_group_chat_users)

    # But: The user is already in the group chat
    telegram_chat = Mock()
    telegram_chat.id = telegram_group_chat_id
    telegram_chat.title = telegram_group_chat_name
    telegram_chat.description = telegram_group_chat_description

    # When: The listener determines this
    added_user = await add_user_to_group_chat(db, telegram_chat, john)
    # Then: The user should not be added to the group chat
    assert added_user is None


@pytest.mark.asyncio
async def test_create_group_chat_and_add_user_if_both_non_existent(db: Session):
    # Given: A group chat doesn't exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_group_chat_description = "Test Chatting"

    # And: We don't have a user
    telegram_chat = Mock()
    telegram_chat.id = telegram_group_chat_id
    telegram_chat.title = telegram_group_chat_name
    telegram_chat.description = telegram_group_chat_description

    current_user = Mock()
    current_user.id = 98765
    current_user.username = "mary"
    current_user.first_name = "Mary"
    current_user.last_name = "Lynn"

    # When: The listener determines this
    added_user = await add_user_to_group_chat(db, telegram_chat, current_user)

    # Then: The group chat is created and the user is added
    created_group_chat = await find_group_chat_by_telegram_group_chat_id(db, telegram_group_chat_id)
    assert created_group_chat is not None

    actual_user = next((user for user in created_group_chat.users if user.username == current_user.username), None)
    assert actual_user.first_name == added_user.first_name
    assert actual_user.last_name == added_user.last_name
    assert actual_user.telegram_user_id == added_user.telegram_user_id
