import pytest
from survey_finder.delivery.retry import RetryPolicy, RetryConfig
from survey_finder.delivery.dispatcher import TelegramDispatcher


def test_retry_policy():
    config = RetryConfig(max_attempts=3, base_delay_seconds=1)
    policy = RetryPolicy(config)

    assert policy.should_retry(0) is True
    assert policy.should_retry(2) is True
    assert policy.should_retry(3) is False

    delay = policy.get_delay(0)
    assert 0.5 <= delay <= 2.0

    delay = policy.get_delay(2)
    assert delay <= 4.0


def test_dispatcher_requires_config():
    # Should not fail on init
    dispatcher = TelegramDispatcher(
        bot_token="test",
        chat_id="test"
    )
    assert dispatcher.bot_token == "test"
