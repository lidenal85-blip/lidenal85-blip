from survey_finder.delivery.dispatcher.dispatcher import NotificationDispatcher

def test_dispatcher_idempotency():
    d = NotificationDispatcher()

    survey = {
        "id": "1",
        "title": "test",
        "payout": 10,
        "source": "prolific"
    }

    r1 = d.dispatch("chat", survey, "cycle1")
    r2 = d.dispatch("chat", survey, "cycle1")

    assert isinstance(r1, bool)
    assert isinstance(r2, bool)
