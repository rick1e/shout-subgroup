import pytest

from shout_subgroup.utils import is_group_chat


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
