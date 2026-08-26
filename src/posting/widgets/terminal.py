"""Reusable terminal widgets for embedded command-line tools."""

from __future__ import annotations

from textual.widget import Widget
from rich.style import Style as RichStyle
from textual_tty import Terminal, TerminalWindow, Window


class TransparentTerminal(Terminal):
    """Render a terminal without painting its default background."""

    DEFAULT_CSS = """
    TransparentTerminal {
        background: transparent;
    }
    """

    def _check_palette(self) -> None:
        super()._check_palette()
        self.styles.background = "transparent"

    def _to_rich(self, style) -> RichStyle:
        rich_style = super()._to_rich(style)
        if style.bg is None or style.bg.mode != "default":
            return rich_style

        return RichStyle(
            color=rich_style.color,
            bold=rich_style.bold,
            dim=rich_style.dim,
            italic=rich_style.italic,
            underline=rich_style.underline,
            blink=rich_style.blink,
            blink2=rich_style.blink2,
            reverse=rich_style.reverse,
            conceal=rich_style.conceal,
            strike=rich_style.strike,
            underline2=rich_style.underline2,
            frame=rich_style.frame,
            encircle=rich_style.encircle,
            overline=rich_style.overline,
            link=rich_style.link,
            meta=rich_style.meta,
        )


class TransparentTerminalWindow(TerminalWindow):
    """A resizable floating window backed by a transparent terminal."""

    def __init__(
        self,
        command: str | list[str],
        title: str | None = None,
        return_focus: Widget | None = None,
        **window_kwargs,
    ) -> None:
        self.terminal = TransparentTerminal(command=command)
        self._restore_geometry = None
        self._return_focus = return_focus
        Window.__init__(
            self,
            self.terminal,
            title=title or str(command),
            **window_kwargs,
        )

    def on_unmount(self) -> None:
        if self._return_focus is not None and self._return_focus.is_attached:
            self.app.call_after_refresh(self._return_focus.focus)
