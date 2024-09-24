import pytest
from sqlalchemy.orm import Session

from conftest import db
from shout_subgroup.exceptions import NotGroupChatError, GroupChatDoesNotExistError
from shout_subgroup.shout import shout_all_members, shout_subgroup_members
from test_helpers import create_test_user, create_test_subgroup, create_test_group_chat


@pytest.mark.asyncio
async def test_shout_all_members(db: Session):
    # Given: A group chat already exists with users
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, jane])

    # When: We shout all group members
    message = await shout_all_members(db, group_chat.telegram_group_chat_id)

    # Then: It mentions them
    assert message == "@johndoe @janedoe "


@pytest.mark.asyncio
async def test_shout_all_members_if_members_have_special_chars_in_username(db: Session):
    # Given: A group chat already exists with users that have special characters in their usernames
    john = create_test_user(db, telegram_user_id=12345, username="john*doe", first_name="John", last_name="Doe")
    dawn = create_test_user(db, telegram_user_id=67890, username="dawn_sun", first_name="Dawn", last_name="Sun")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, dawn])

    # When: We shout all group members
    message = await shout_all_members(db, group_chat.telegram_group_chat_id)

    # Then: It mentions them
    assert message == "@john\\*doe @dawn\\_sun "


@pytest.mark.asyncio
async def test_shout_all_members_handles_no_registered_members(db: Session):
    # Given: A group chat exists, but there are no members in it
    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [])

    # When: We shout all group members
    message = await shout_all_members(db, group_chat.telegram_group_chat_id)

    # Then: It mentions them
    assert message == "I don't know any members in this chat. If you want me to register someone ask them to send a message."


@pytest.mark.asyncio
async def test_shout_subgroup_members(db: Session):
    # Given: A group chat already exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, jane])

    # And: the group chat has a subgroup with members
    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, [john])

    # When: We shout all subgroup members
    message = await shout_subgroup_members(db, group_chat.telegram_group_chat_id, subgroup_name)

    # Then: It mentions them
    assert message == "@johndoe "


@pytest.mark.asyncio
async def test_shout_subgroup_members_only_mentions_members_for_group_chat(db: Session):
    # Given: A multiple group chats already exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")
    sue = create_test_user(db, telegram_user_id=54321, username="suedoe", first_name="Sue", last_name="Doe")

    telegram_group_chat_a_id = -123456789
    group_chat_a = create_test_group_chat(db, telegram_group_chat_a_id, "Group Chat A", [john, jane])
    telegram_group_chat_b_id = -987654321
    group_chat_b = create_test_group_chat(db, telegram_group_chat_b_id, "Group Chat B", [jane, sue])

    # And: The group chats have a subgroup each with the same name
    subgroup_name = "Party"
    create_test_subgroup(db, group_chat_a.group_chat_id, subgroup_name, [john])
    create_test_subgroup(db, group_chat_b.group_chat_id, subgroup_name, [sue])

    # When: We shout all subgroup members for a group chat
    message = await shout_subgroup_members(db, group_chat_a.telegram_group_chat_id, subgroup_name)

    # Then: It mentions them
    assert message == "@johndoe "


@pytest.mark.asyncio
async def test_shout_subgroup_members_handles_no_subgroup_members(db: Session):
    # Given: A group chat already exists
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")
    jane = create_test_user(db, telegram_user_id=67890, username="janedoe", first_name="Jane", last_name="Doe")

    telegram_group_chat_id = -123456789
    group_chat = create_test_group_chat(db, telegram_group_chat_id, "Group Chat", [john, jane])

    # And: the group chat has a subgroup without any members
    subgroup_name = "Archery"
    create_test_subgroup(db, group_chat.group_chat_id, subgroup_name, [])

    # When: We shout all subgroup members
    message = await shout_subgroup_members(db, group_chat.telegram_group_chat_id, subgroup_name)

    # Then: It mentions them
    assert message == "'Archery' subgroup has no members, use /group to add members."


@pytest.mark.asyncio
async def test_shout_subgroup_members_throws_not_group_chat_exception(db: Session):
    # Given: The telegram chat is not a group chat
    user_chat_id = 123

    # When: We try to shout subgroup members
    # Then: An exception is thrown
    with pytest.raises(NotGroupChatError) as ex:
        await shout_subgroup_members(db, user_chat_id, "Archery")

    assert str(user_chat_id) in ex.value.message


@pytest.mark.asyncio
async def test_shout_subgroup_members_throws_group_chat_does_not_exist_exception(db: Session):
    # Given: The group chat does not exist
    non_existent_group_chat = -123

    # When: We try to shout subgroup members
    # Then: An exception is thrown
    with pytest.raises(GroupChatDoesNotExistError) as ex:
        await shout_subgroup_members(db, non_existent_group_chat, "Archery")

    assert str(non_existent_group_chat) in ex.value.message
