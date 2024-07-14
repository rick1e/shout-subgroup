import pytest
from sqlalchemy.orm import Session

from shout_subgroup.exceptions import NotGroupChatError, SubGroupDoesNotExistsError
from shout_subgroup.list_subgroup import list_subgroups, list_subgroup_members
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


@pytest.mark.asyncio
async def test_list_subgroup_members(db: Session):
    # Given: A subgroup exist with members

    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, subgroup_users)

    # When: We list the members
    result = await list_subgroup_members(db, group_chat.telegram_group_chat_id, subgroup_name)

    # Then: The members are shown
    assert len(result) == len(subgroup_users)

    result_names = [member.username for member in result]
    usernames = [user.username for user in subgroup_users]
    assert set(result_names) == set(usernames)


@pytest.mark.asyncio
async def test_list_subgroup_that_has_no_members(db: Session):
    # Given: A subgroup exist with no members
    telegram_group_chat_id = -123456789
    subgroup_users = []

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, subgroup_users)

    # When: We list the members
    result = await list_subgroup_members(db, group_chat.telegram_group_chat_id, subgroup_name)

    # Then: No members are there
    assert result == []


@pytest.mark.asyncio
async def test_list_subgroup_members_throws_not_group_chat_exception(db: Session):
    # Given: The telegram chat is not a group chat
    user_chat_id = 123

    # When: We try to list the subgroups
    # Then: An exception is thrown
    with pytest.raises(NotGroupChatError) as ex:
        await list_subgroup_members(db, user_chat_id, "mock-subgroup")

    assert str(user_chat_id) in ex.value.message


@pytest.mark.asyncio
async def test_list_subgroup_members_throws_not_subgroup_does_not_exist_exception(db: Session):
    # Given: Subgroup doesn't exist
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", subgroup_users)

    non_existent_subgroup_name = "nonexistent-subgroup"
    # When: We try to list the subgroups
    # Then: An exception is thrown
    with pytest.raises(SubGroupDoesNotExistsError) as ex:
        await list_subgroup_members(db, group_chat.telegram_group_chat_id, non_existent_subgroup_name)

    assert str(non_existent_subgroup_name) in ex.value.message
    assert str(group_chat.telegram_group_chat_id) in ex.value.message
