from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from shout_subgroup.exceptions import UserDoesNotExistsError
from shout_subgroup.utils import is_group_chat, replace_me_mentions, get_user_id_from_mention, \
    UserIdMentionMapping, get_mention_from_user_id_mention_mappings, create_mention_from_user_id
from test_helpers import create_test_user


@pytest.mark.asyncio
@pytest.mark.parametrize("telegram_chat_id, expected_result", [
    (-123, True),  # Group chat
    (456, False),  # Non-group chat
])
async def test_is_group_chat(telegram_chat_id, expected_result):
    # When: We check if it's a group chat
    result = await is_group_chat(telegram_chat_id)

    # Then: The correct value is returned
    assert result == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize("usernames, expected_result", [
    ({"@me", "@pablo", "@garcia"}, {"richie", "pablo", "garcia"}),  # @me is present
    ({"@ME", "@pablo", "@garcia"}, {"richie", "pablo", "garcia"}),  # Uppercase
    ({"@mE", "@pablo", "@garcia"}, {"richie", "pablo", "garcia"}),  # Mixed case
    ({"@richie", "@pablo", "@garcia"}, {"richie", "pablo", "garcia"}),  # No @me
    ({}, set()),  # Empty set
])
async def test_format_telegram_usernames(usernames, expected_result):
    # Given: We have the telegram user
    telegram_user = Mock()
    telegram_user.id = 123
    telegram_user.first_name = "Richard"
    telegram_user.username = "richie"

    # When: We format the usernames
    result = await replace_me_mentions(usernames, telegram_user)

    # Then: The correct value is returned
    assert result == expected_result


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_username(db: Session):
    # Given: A users exist within our system
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")

    # And: We mention them by username
    mention = "@johndoe"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The correct user_id is found
    assert result == UserIdMentionMapping(mention=mention, user_id=john.user_id)


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_username_non_existent_user(db: Session):
    # Given: A users exist within our system
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")

    # And: We mention them by username
    mention = "@sue"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The no user_id is found
    assert result == UserIdMentionMapping(mention=mention, user_id=None)


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_markdown(db: Session):
    # Given: A users exist within our system
    jane = create_test_user(db, telegram_user_id=12345, username=None, first_name="Jane", last_name="Doe")

    # And: We mention them by username
    mention = "[Jane](tg://user?id=12345)"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The correct user_id is found
    assert result == UserIdMentionMapping(mention=mention, user_id=jane.user_id)


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_markdown_non_existent_user(db: Session):
    # Given: A users exist within our system
    create_test_user(db, telegram_user_id=12345, username=None, first_name="Jane", last_name="Doe")

    # And: We mention them by username
    mention = "[Jane](tg://user?id=98765)"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The correct user_id is found
    assert result == UserIdMentionMapping(mention=mention, user_id=None)


@pytest.mark.asyncio
async def test_get_mention_from_user_id_single_match():

    # Given: We have mappings
    user_id = "123"
    mention = "@user123"

    mapping_a = UserIdMentionMapping(user_id=user_id, mention=mention)
    mapping_b = UserIdMentionMapping(user_id="876", mention="@user876")

    users_ids_and_mentions = {mapping_a, mapping_b}

    # When: We get the mention from the id
    result = await get_mention_from_user_id_mention_mappings(user_id, users_ids_and_mentions)

    # Then: it finds the mapping
    assert result == mapping_a.mention


@pytest.mark.asyncio
async def test_get_mention_from_user_id_no_match():

    # Given: We have mappings
    user_id = "123"
    mention = "@user123"

    mapping_a = UserIdMentionMapping(user_id=user_id, mention=mention)
    mapping_b = UserIdMentionMapping(user_id="876", mention="@user876")

    users_ids_and_mentions = {mapping_a, mapping_b}

    # When: We get the mention from a non-existent id
    non_existent_user_id = "abc999"
    result = await get_mention_from_user_id_mention_mappings(non_existent_user_id, users_ids_and_mentions)

    # Then: it finds the mapping
    assert not result


@pytest.mark.asyncio
async def test_create_mention_from_user_id(db: Session):

    # Given: A users exist within our system
    jane = create_test_user(db, telegram_user_id=12345, username="janey", first_name="Jane", last_name="Doe")

    # When: We create a mention from the user ID
    result = await create_mention_from_user_id(db, jane.user_id)

    # Then: The result should be a mention using the username
    assert result == "@janey"


@pytest.mark.asyncio
async def test_create_mention_from_user_id_without_username(db: Session):
    # Given: A user exists in the system without a username, but with a first name and Telegram user ID
    john = create_test_user(db, telegram_user_id=67890, username=None, first_name="John", last_name="Doe")

    # When: We create a mention from the user ID
    result = await create_mention_from_user_id(db, john.user_id)

    # Then: The result should be a mention using the first name and Telegram user ID
    assert result == "[John](tg://user?id=67890)"


@pytest.mark.asyncio
async def test_create_mention_from_nonexistent_user_id(db: Session):
    # Given: A non-existent user ID is provided
    non_existent_user_id = "non_existent_user_id"

    # When: We attempt to create a mention from the non-existent user ID
    # Then: The function should raise an appropriate exception
    with pytest.raises(UserDoesNotExistsError) as exc:
        await create_mention_from_user_id(db, non_existent_user_id)

    assert exc.value.message == f"Can not create mention for user id {non_existent_user_id} because it does not exist"