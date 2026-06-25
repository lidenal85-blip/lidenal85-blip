import pytest
from survey_finder.delivery.dispatcher import TelegramDispatcher


def test_dispatcher_requires_config():
    dispatcher = TelegramDispatcher(
        bot_token="test",
        chat_id="test"
    )
    assert dispatcher.bot_token == "test"
