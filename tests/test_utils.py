from unittest.mock import Mock

import pytest

from shout_subgroup.utils import is_group_chat, format_telegram_usernames


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
