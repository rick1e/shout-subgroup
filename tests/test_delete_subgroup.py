import pytest
from sqlalchemy.orm import Session

from shout_subgroup.delete_subgroup import remove_subgroup
from shout_subgroup.exceptions import SubGroupDoesNotExistsError, NotGroupChatError
from shout_subgroup.repository import find_subgroup_by_telegram_group_chat_id_and_subgroup_name
from test_helpers import create_test_user, create_test_group_chat, create_test_subgroup


@pytest.mark.asyncio
async def test_remove_subgroup(db: Session):
    # Given: A group chat and subgroup exist
    telegram_chat_id = -123456789
    subgroup_name = "Archery"

    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    group_chat = create_test_group_chat(db, telegram_chat_id, "Group Chat", [john, jane])
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, [john, jane])

    # When: The subgroup is removed
    result = await remove_subgroup(db, telegram_chat_id, subgroup_name)

    # Then: The result should be True
    assert result is True

    # And: The subgroup no longer exists
    subgroup = await find_subgroup_by_telegram_group_chat_id_and_subgroup_name(db, telegram_chat_id, subgroup_name)
    assert subgroup is None


@pytest.mark.asyncio
async def test_remove_subgroup_that_does_not_exist(db: Session):
    # Given: A group chat exists but the subgroup does not
    telegram_chat_id = -123456789
    subgroup_name = "Archery"

    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    create_test_group_chat(db, telegram_chat_id, "Group Chat", [john, jane])

    # When: Attempting to remove a non-existent subgroup
    with pytest.raises(SubGroupDoesNotExistsError):
        await remove_subgroup(db, telegram_chat_id, subgroup_name)


@pytest.mark.asyncio
async def test_remove_subgroup_that_not_in_a_group_chat(db: Session):
    # Given: The chat ID is not a group chat
    telegram_chat_id = 123  # Assume positive IDs are not group chats
    subgroup_name = "Archery"

    create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")

    # When: Attempting to remove a subgroup from a non-group chat
    with pytest.raises(NotGroupChatError):
        await remove_subgroup(db, telegram_chat_id, subgroup_name)
