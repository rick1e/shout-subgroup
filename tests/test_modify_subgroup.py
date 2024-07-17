import pytest
from sqlalchemy.orm import Session

from shout_subgroup.exceptions import SubGroupDoesNotExistsError, UserDoesNotExistsError, NotGroupChatError
from shout_subgroup.modify_subgroup import add_users_to_existing_subgroup, does_subgroup_exist
from test_helpers import create_test_user, create_test_group_chat, create_test_subgroup


class MockTelegramChat:
    def __init__(self, id, title, description):
        self.id = id
        self.title = title
        self.description = description


@pytest.mark.asyncio
async def test_add_users_to_existing_subgroup(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We add a new member to the group
    subgroup = await add_users_to_existing_subgroup(db, telegram_group_chat_id, subgroup_name, {betty.username})

    # Then: It's added correctly
    assert len(subgroup.users) == 3

    actual_usernames = [user.username for user in subgroup.users]
    expected_subgroup_users = [john, jane, betty]
    expected_usernames = [user.username for user in expected_subgroup_users]
    assert set(actual_usernames) == set(expected_usernames)


@pytest.mark.asyncio
async def test_add_users_to_existing_subgroup_when_provided_user_already_in_group(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    betty = create_test_user(db, telegram_user_id=87654, username="betty", first_name="Betty", last_name="White")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We add a new member and an existing member to the group
    members_to_add = {jane.username, betty.username}
    subgroup = await add_users_to_existing_subgroup(db, telegram_group_chat_id, subgroup_name, members_to_add)

    # Then: It's added correctly
    assert len(subgroup.users) == 3

    actual_usernames = [user.username for user in subgroup.users]
    expected_subgroup_users = [john, jane, betty]
    expected_usernames = [user.username for user in expected_subgroup_users]
    assert set(actual_usernames) == set(expected_usernames)


@pytest.mark.asyncio
async def test_add_users_to_existing_subgroup_throws_exception_for_non_existent_subgroup(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We try to modify a non-existent subgroup
    non_existent_subgroup_name = "Party"
    with pytest.raises(SubGroupDoesNotExistsError) as ex:
        await add_users_to_existing_subgroup(db, telegram_group_chat_id, non_existent_subgroup_name, {john.username})

    # Then: The exception is thrown with correct message
    assert non_existent_subgroup_name in ex.value.message
    assert str(group_chat.telegram_group_chat_id) in ex.value.message


@pytest.mark.asyncio
async def test_add_users_to_existing_subgroup_throws_exception_for_non_existent_user(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We try to add a non-existent user
    non_existent_user = {"mary"}
    with pytest.raises(UserDoesNotExistsError) as ex:
        await add_users_to_existing_subgroup(db, telegram_group_chat_id, subgroup_name, non_existent_user)

    # Then: The exception is thrown with correct message
    assert "usernames are not" in ex.value.message


@pytest.mark.asyncio
async def test_does_subgroup_exist(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We look for the subgroup
    exists = await does_subgroup_exist(db, telegram_group_chat_id, subgroup_name)

    # Then: It exists
    assert exists


@pytest.mark.asyncio
async def test_does_subgroup_does_not_exist(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We look for the non-existent subgroup
    non_existent_subgroup_name = "Party"
    exists = await does_subgroup_exist(db, telegram_group_chat_id, non_existent_subgroup_name)

    # Then: It doesn't exists
    assert not exists


@pytest.mark.asyncio
async def test_does_subgroup_exist_throws_exception_when_group_chat_does_not_exist(db: Session):
    # Given: A subgroup exist with members
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    initial_subgroup_users = [john, jane]

    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", initial_subgroup_users)

    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, initial_subgroup_users)

    # When: We look for the subgroup
    user_chat_id = 123  # Users have positive integers for ids
    with pytest.raises(NotGroupChatError) as ex:
        await does_subgroup_exist(db, user_chat_id, subgroup_name)

    # Then: It exists
    assert str(user_chat_id) in ex.value.message
