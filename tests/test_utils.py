from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from shout_subgroup.utils import is_group_chat, format_telegram_usernames, get_user_id_from_mention
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
    result = await format_telegram_usernames(usernames, telegram_user)

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
    assert result == john.user_id


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_username_non_existent_user(db: Session):
    # Given: A users exist within our system
    john = create_test_user(db, telegram_user_id=12345, username="johndoe", first_name="John", last_name="Doe")

    # And: We mention them by username
    mention = "@sue"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The no user_id is found
    assert not result


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_markdown(db: Session):
    # Given: A users exist within our system
    jane = create_test_user(db, telegram_user_id=12345, username=None, first_name="Jane", last_name="Doe")

    # And: We mention them by username
    mention = "[Jane](tg://user?id=12345)"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The correct user_id is found
    assert result == jane.user_id


@pytest.mark.asyncio
async def test_get_user_id_from_mention_with_markdown_non_existent_user(db: Session):
    # Given: A users exist within our system
    jane = create_test_user(db, telegram_user_id=12345, username=None, first_name="Jane", last_name="Doe")

    # And: We mention them by username
    mention = "[Jane](tg://user?id=98765)"

    # When: We convert from their mention text to their id
    result = await get_user_id_from_mention(db, mention)

    # Then: The correct user_id is found
    assert not result
