from rich.style import Style
from textual import events
from textual.theme import Theme
from textual.widgets import Input


from posting.config import SETTINGS


class PostingInput(Input):
    async def _on_key(self, event: events.Key) -> None:
        """Keep inputs focusable while disabling direct editing in Posting."""
        if event.key == self.app.settings.leader:
            event.stop()
            event.prevent_default()
            self.app.action_leader()
            return
        if event.is_printable:
            # Let navigation bindings on parent widgets see keys such as j/k.
            event.prevent_default()
            return
        if event.key in {"backspace", "delete", "enter", "ctrl+v", "shift+insert"}:
            event.stop()
            event.prevent_default()
            return
        await super()._on_key(event)

    def _on_paste(self, event: events.Paste) -> None:
        event.stop()
        event.prevent_default()

    def on_mount(self) -> None:
        self.cursor_blink = SETTINGS.get().text_input.blinking_cursor

        self._theme_cursor_style: Style | None = None

        self.on_theme_change(self.app.current_theme)
        self.app.theme_changed_signal.subscribe(self, self.on_theme_change)

    @property
    def cursor_style(self) -> Style:
        return (
            self._theme_cursor_style
            if self._theme_cursor_style is not None
            else self.get_component_rich_style("input--cursor")
        )

    def on_theme_change(self, theme: Theme) -> None:
        cursor_style = theme.variables.get("input-cursor")
        self._theme_cursor_style = Style.parse(cursor_style) if cursor_style else None
        self.refresh()
