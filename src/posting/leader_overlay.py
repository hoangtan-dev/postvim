from textual import events
from textual.screen import ModalScreen


class LeaderOverlay(ModalScreen[str | None]):
    """Capture a key sequence following the configured leader key."""

    DEFAULT_CSS = """
    LeaderOverlay {
        background: transparent;
    }
    """

    def __init__(self, leader: str, actions: dict[tuple[str, ...], str]) -> None:
        super().__init__()
        self.leader = leader
        self.actions = actions
        self._sequence: tuple[str, ...] = ()

    def on_mount(self) -> None:
        self.styles.background = "transparent"

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()

        sequence = (*self._sequence, event.key)
        action = self.actions.get(sequence)
        if action is not None:
            self.dismiss(action)
            return

        if any(candidate[: len(sequence)] == sequence for candidate in self.actions):
            self._sequence = sequence
            return

        self.dismiss(None)
