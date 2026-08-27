from textual import events
from textual.screen import ModalScreen


class LeaderOverlay(ModalScreen[str | None]):
    """Capture the key following the configured leader key."""

    DEFAULT_CSS = """
    LeaderOverlay {
        background: transparent;
    }
    """

    def __init__(self, leader: str) -> None:
        super().__init__()
        self.leader = leader

    def on_mount(self) -> None:
        self.styles.background = "transparent"

    def on_key(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()

        if event.key == self.leader:
            self.dismiss("search")
        elif event.key == "r":
            self.dismiss("send")
        else:
            self.dismiss(None)
