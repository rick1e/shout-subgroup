import pytest
from sqlalchemy.orm import Session

from shout_subgroup.exceptions import NotGroupChatError
from shout_subgroup.list_subgroup import list_subgroups
from test_helpers import (create_test_user, create_test_group_chat,
                          create_test_subgroup)


@pytest.mark.asyncio
async def test_list_subgroup(db: Session):
    # Given: A group chat already exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, jane])

    # And: the group chat has a subgroup with members
    subgroup_names = ["Archery", "Bowling", "Cricket"]
    for name in subgroup_names:
        create_test_subgroup(db, group_chat.group_chat_id, name, [john])

    # When: We list the subgroups
    result = await list_subgroups(db, group_chat.telegram_group_chat_id)

    # Then: All of them should appear
    assert len(result) == len(subgroup_names)
    result_names = [sub.name for sub in result]
    assert set(result_names) == set(subgroup_names)


@pytest.mark.asyncio
async def test_list_subgroup_for_no_subgroups(db: Session):
    # Given: A group chat already exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, jane])

    # But: No subgroups exists in the group chat

    # When: We list the subgroups
    result = await list_subgroups(db, group_chat.telegram_group_chat_id)

    # Then: An empty string is returned
    assert result == []


@pytest.mark.asyncio
async def test_list_subgroup_throws_not_group_chat_exception(db: Session):
    # Given: The telegram chat is not a group chat
    user_chat_id = 123

    # When: We try to list the subgroups
    # Then: An exception is thrown
    with pytest.raises(NotGroupChatError) as ex:
        await list_subgroups(db, user_chat_id)

    assert str(user_chat_id) in ex.value.message
