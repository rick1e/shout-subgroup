from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session
from telegram import Chat

from shout_subgroup.exceptions import SubGroupDoesNotExistsError, UserDoesNotExistsError, NotGroupChatError
from shout_subgroup.group_chat_listener import add_user_to_group_chat, remove_user_from_group_chat
from shout_subgroup.models import UserModel
from shout_subgroup.modify_subgroup import add_users_to_existing_subgroup, remove_users_from_existing_subgroup
from shout_subgroup.repository import find_group_chat_by_telegram_group_chat_id, find_all_users_in_subgroup
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
    betty.user_id = 87654
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
    current_user.user_id = 98765
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


@pytest.mark.asyncio
async def test_add_user_to_group_throws_exception_for_non_group_chat(db: Session):
    # Given: A group chat exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_group_chat_description = "Test Chatting"

    initial_group_chat_users = [john, jane]
    group_chat = create_test_group_chat(db, telegram_group_chat_id, telegram_group_chat_name, initial_group_chat_users)

    # But: The user is not in the group chat and the chat is not a group chat
    betty = UserModel(
        telegram_user_id=87654,
        username="betty",
        first_name="Betty",
        last_name="White"
    )

    not_telegram_group_chat_id = 123456789

    telegram_chat = Mock()
    telegram_chat.id = not_telegram_group_chat_id
    telegram_chat.title = ""
    telegram_chat.description = ""

    # When: The listener determines this

    # When: We try to add the user to a not group chat
    with pytest.raises(NotGroupChatError) as ex:
        added_user = await add_user_to_group_chat(db, telegram_chat, betty)

    # Then: The exception is thrown with correct message and the user was not added 
    assert str(not_telegram_group_chat_id) in ex.value.message
    actual_user = next((user for user in group_chat.users if user.username == betty.username), None)
    assert actual_user is None


@pytest.mark.asyncio
async def test_remove_user_from_group_chat(db: Session):
    # Given: A group chat exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_group_chat_description = "Test Chatting"

    initial_group_chat_users = [john, jane]
    group_chat = create_test_group_chat(db, telegram_group_chat_id, telegram_group_chat_name, initial_group_chat_users)

    # And: There are sub groups with the user in it
    subgroup_names = ["Archery", "Bowling", "Cricket"]
    for name in subgroup_names:
        create_test_subgroup(db, group_chat.group_chat_id, name, [john])

    # When: We try to remove the user from the group chat
    betty = Mock()
    betty.user_id = 12345
    betty.username = "johndoe"
    betty.first_name = "John"
    betty.last_name = "Doe"

    telegram_chat = Mock()
    telegram_chat.id = telegram_group_chat_id
    telegram_chat.title = telegram_group_chat_name
    telegram_chat.description = telegram_group_chat_description

    # When: The listener determines this
    removed_user = await remove_user_from_group_chat(db, telegram_chat, betty)

    # Then: The user is removed from the group chat
    assert removed_user.user_id is not None
    actual_user = next((user for user in group_chat.users if user.username == betty.username), None)
    assert actual_user is None

    # And: The user is removed from all sub groups
    for name in subgroup_names:
        users = await find_all_users_in_subgroup(db, telegram_group_chat_id, name)
        for user in users:
            assert user.username is not betty.username

    # pass


@pytest.mark.asyncio
async def test_remove_user_from_group_chat_if_not_in_group_chat(db: Session):

    # Given: A group chat exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    telegram_group_chat_name = "Group Chat"
    telegram_chat = Mock()
    telegram_chat.id = telegram_group_chat_id
    telegram_chat.title = telegram_group_chat_name
    telegram_chat.description = "Testing Chat"

    initial_group_chat_users = [john]
    create_test_group_chat(db, telegram_group_chat_id, telegram_group_chat_name, initial_group_chat_users)

    # And: A user leaves the group chat before they were registered by the bot
    betty = Mock()
    betty.user_id = 12345
    betty.username = "bettysue"
    betty.first_name = "Betty"
    betty.last_name = "Sue"

    # When: The listener detects this
    removed_user = await remove_user_from_group_chat(db, telegram_chat, betty)

    # Then: A None should be returned b/c the user was never registered
    assert removed_user is None


@pytest.mark.asyncio
async def test_remove_user_from_group_chat_throws_exception_for_non_group_chat(db: Session):
    # Given: A individual chat exists
    individual_chat = 12345
    telegram_chat = Mock()
    telegram_chat.id = individual_chat
    telegram_chat.title = "Betty"
    telegram_chat.description = "Betty Chat"

    # And: A user exists
    betty = Mock()
    betty.user_id = 12345
    betty.username = "bettysue"
    betty.first_name = "Betty"
    betty.last_name = "Sue"

    # When: The listener sees a user leave the chat
    with pytest.raises(NotGroupChatError) as ex:
        await remove_user_from_group_chat(db, telegram_chat, betty)

    # Then: An exception is thrown
    assert ex.value.message == f"Can't remove user from chat because telegram chat id {telegram_chat.id} is not a group chat."
