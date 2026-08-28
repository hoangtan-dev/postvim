import os
import tempfile
from collections.abc import Callable

from textual_tty import Terminal

from posting.widgets.terminal import TransparentTerminalWindow
from posting.yaml import dump
import yaml


class DictEditorWindow(TransparentTerminalWindow):
    """Edit a string mapping in a floating Neovim window."""

    NVIM_APPNAME = "posting"

    DEFAULT_CSS = """\
DictEditorWindow {
    width: 120;
    height: 15;
    background: transparent;
    border: none;
}

DictEditorWindow:focus-within {
    background: transparent;
}

DictEditorWindow > #header {
    height: 1;
    background: #01050a;
    color: $foreground-muted;
}

DictEditorWindow:focus-within > #header {
    background: #01050a;
}

DictEditorWindow > #header > TitleBar {
    content-align: center middle;
    padding: 0 1;
    color: #c4b5fd;
}

DictEditorWindow > #header > CloseButton {
    color: $foreground-muted;
    background: transparent;
    content-align: center middle;
}

DictEditorWindow > #header > CloseButton:hover {
    background: $error 70%;
}

DictEditorWindow > #content,
DictEditorWindow > #footer,
DictEditorWindow > #content > TransparentTerminal {
    background: transparent;
}

DictEditorWindow > #footer {
    display: none;
}
"""

    def __init__(
        self,
        return_focus,
        values: dict[str, str],
        on_save: Callable[[dict[str, str | None]], None],
        title: str,
    ) -> None:
        self.return_focus = return_focus
        self.on_save = on_save
        self.file_name = ""
        self._result_read = False

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            self.file_name = temp_file.name
            temp_file.write(dump(values, None, sort_keys=False))

        super().__init__(
            command=["env", f"NVIM_APPNAME={self.NVIM_APPNAME}", "nvim", self.file_name],
            title=title,
            return_focus=return_focus,
            starting_horizontal="center",
            starting_vertical="middle",
        )

    def on_terminal_process_exited(self, message: Terminal.ProcessExited) -> None:
        if message.exit_code == 0 and not self._result_read:
            try:
                with open(self.file_name, encoding="utf-8") as file:
                    values = yaml.safe_load(file) or {}
                if not isinstance(values, dict):
                    raise ValueError("content must be a YAML mapping")
                if any(not isinstance(key, str) for key in values):
                    raise ValueError("all keys must be strings")
                if any(
                    value is not None
                    and not isinstance(value, (str, int, float, bool))
                    for value in values.values()
                ):
                    raise ValueError("all values must be scalar")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                self.app.notify(str(exc), title="Invalid mapping", severity="error")
            else:
                self.on_save(
                    {
                        str(key): None if value is None else str(value)
                        for key, value in values.items()
                    }
                )
            self._result_read = True
        elif message.exit_code != 0:
            self.app.notify(
                f"Neovim exited with status {message.exit_code}.", severity="error"
            )
        super().on_terminal_process_exited(message)

    def on_unmount(self) -> None:
        super().on_unmount()
        if self.file_name and os.path.exists(self.file_name):
            os.remove(self.file_name)
