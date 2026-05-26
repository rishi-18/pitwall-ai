"""
Unit tests for room state transitions.
"""


class RoomStateMachine:

    VALID_TRANSITIONS = {
        "LOBBY": ["STARTING"],
        "STARTING": ["LIVE", "LOBBY"],
        "LIVE": ["PAUSED", "ENDED"],
        "PAUSED": ["LIVE", "ENDED"],
        "ENDED": [],
    }

    def __init__(self):

        self.state = "LOBBY"

    def transition(
        self,
        new_state: str
    ) -> bool:

        if new_state in self.VALID_TRANSITIONS.get(
            self.state,
            []
        ):
            self.state = new_state
            return True

        return False


def test_lobby_to_starting():

    sm = RoomStateMachine()

    assert sm.transition("STARTING") is True

    assert sm.state == "STARTING"


def test_invalid_transition_rejected():

    sm = RoomStateMachine()

    assert sm.transition("ENDED") is False

    assert sm.state == "LOBBY"
