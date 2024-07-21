import pytest
from sqlalchemy.orm import Session

from shout_subgroup.exceptions import SubGroupDoesNotExistsError, UserDoesNotExistsError, NotGroupChatError
from shout_subgroup.modify_subgroup import add_users_to_existing_subgroup, remove_users_from_existing_subgroup
from test_helpers import create_test_user, create_test_group_chat, create_test_subgroup


class MockTelegramChat:
    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description


@pytest.mark.asyncio
async def test_remove_users_from_existing_subgroup(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane, betty]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We remove a member from the subgroup
    users_to_remove = {john.username}
    subgroup = await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup_name, users_to_remove)

    # Then: The subgroup doesn't have the member anymore
    assert len(subgroup.users) == 2

    actual_usernames = [user.username for user in subgroup.users]
    expected_subgroup_users = [jane, betty]
    expected_usernames = [user.username for user in expected_subgroup_users]
    assert set(actual_usernames) == set(expected_usernames)


@pytest.mark.asyncio
async def test_remove_a_user_who_is_not_in_the_subgroup(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [jane, betty]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We remove a member who isn't in the group
    users_to_remove = {john.username}
    subgroup = await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup_name, users_to_remove)

    # Then: The subgroup is unchanged
    assert len(subgroup.users) == len(initial_subgroup_users)

    actual_usernames = [user.username for user in subgroup.users]
    expected_subgroup_users = [jane, betty]
    expected_usernames = [user.username for user in expected_subgroup_users]
    assert set(actual_usernames) == set(expected_usernames)


@pytest.mark.asyncio
async def test_remove_all_users_from_existing_subgroup(db: Session):
    # Given: A subgroup exist with members
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [jane, betty]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We remove all the members
    users_to_remove = {jane.username, betty.username}
    subgroup = await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup_name, users_to_remove)

    # Then: The subgroup is empty
    assert len(subgroup.users) == 0


@pytest.mark.asyncio
async def test_remove_users_from_existing_subgroup_when_group_is_empty(db: Session):
    # Given: A subgroup exist with members
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = []

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We remove a user
    members_to_remove = {jane.username, betty.username}
    subgroup = await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup_name, members_to_remove)

    # Then: The group remains empty
    assert len(subgroup.users) == 0


@pytest.mark.asyncio
async def test_remove_users_from_existing_subgroup_throws_exception_for_non_group_chat_id(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We try to remove a user
    user_chat_id = 1234
    with pytest.raises(NotGroupChatError) as ex:
        await remove_users_from_existing_subgroup(db, user_chat_id, subgroup_name, {john.username})

    # Then: The exception is thrown with correct message
    assert str(user_chat_id) in ex.value.message


@pytest.mark.asyncio
async def test_remove_users_from_existing_subgroup_throws_exception_for_non_existent_subgroup(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We try to remove a user from a non-existent subgroup
    non_existent_subgroup_name = "Party"
    with pytest.raises(SubGroupDoesNotExistsError) as ex:
        await remove_users_from_existing_subgroup(db, telegram_group_chat_id, non_existent_subgroup_name,
                                                  {john.username})

    # Then: The exception is thrown with correct message
    assert non_existent_subgroup_name in ex.value.message
    assert str(group_chat.telegram_group_chat_id) in ex.value.message


@pytest.mark.asyncio
async def test_remove_users_from_existing_subgroup_throws_exception_for_non_existent_user(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We try to remove a non-existent user
    non_existent_user = {"mary"}
    with pytest.raises(UserDoesNotExistsError) as ex:
        await remove_users_from_existing_subgroup(db, telegram_group_chat_id, subgroup_name, non_existent_user)

    # Then: The exception is thrown with correct message
    assert "usernames are not" in ex.value.message
