import os
import tempfile

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, Label
from textual_tty import Terminal
from posting.help_data import HelpData

from posting.widgets.center_middle import CenterMiddle
from posting.widgets.request.form_editor import FormEditor
from posting.widgets.select import PostingSelect
from posting.widgets.terminal import TransparentTerminalWindow
from posting.widgets.text_area import PostingTextArea, TextAreaFooter, TextEditor


class RequestBodyEditor(Vertical):
    """
    A container for the request body text area and the request body type selector.
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="request-body-type-select-container"):
            yield PostingSelect(
                # These values are also referred to inside MainScreen.
                # When we load a request, we need to set the correct
                # value in the select.
                options=[
                    ("None", "no-body-label"),
                    ("Raw (json, text, etc.)", "text-body-editor"),
                    ("Form data (x-www-form-urlencoded)", "form-body-editor"),
                ],
                id="request-body-type-select",
                allow_blank=False,
            )
        with ContentSwitcher(
            initial="no-body-label",
            id="request-body-type-content-switcher",
        ):
            yield CenterMiddle(
                Label("No request body"),
                id="no-body-label",
            )
            text_area = RequestBodyTextArea(language="json", read_only=True)
            yield TextEditor(
                text_area=text_area,
                footer=TextAreaFooter(text_area),
                id="text-body-editor",
            )
            yield FormEditor(
                id="form-body-editor",
            )


class RequestBodyEditorWindow(TransparentTerminalWindow):
    """A floating Neovim editor for a raw request body."""

    DEFAULT_CSS = """
    RequestBodyEditorWindow {
        position: absolute;
        width: 120;
        height: 5;
        background: transparent;
        border: none;
    }

    RequestBodyEditorWindow:focus-within {
        background: transparent;
    }

    RequestBodyEditorWindow > #header {
        height: 1;
        background: #01050a;
        color: $foreground-muted;
    }

    RequestBodyEditorWindow:focus-within > #header {
        background: #01050a;
    }

    RequestBodyEditorWindow > #header > TitleBar {
        content-align: center middle;
        padding: 0 1;
        color: #c4b5fd;
    }

    RequestBodyEditorWindow > #header > CloseButton {
        color: $foreground-muted;
        background: transparent;
        content-align: center middle;
    }

    RequestBodyEditorWindow > #header > CloseButton:hover {
        background: $error 70%;
    }

    RequestBodyEditorWindow > #content,
    RequestBodyEditorWindow > #footer,
    RequestBodyEditorWindow > #content > TransparentTerminal {
        background: transparent;
    }

    RequestBodyEditorWindow > #footer {
        display: none;
    }
    """

    NVIM_APPNAME = "posting"

    def __init__(self, text_area: "RequestBodyTextArea", file_name: str) -> None:
        self.text_area = text_area
        self.file_name = file_name
        self._result_read = False
        super().__init__(
            command=["env", f"NVIM_APPNAME={self.NVIM_APPNAME}", "nvim", file_name],
            title="Edit Request Body",
            return_focus=text_area,
            starting_horizontal="center",
            starting_vertical="middle",
        )
        body_lines = max(1, text_area.text.count("\n") + 1)
        self.styles.height = min(max(body_lines + 6, 10), 30)

    def on_terminal_process_exited(self, message: Terminal.ProcessExited) -> None:
        if message.exit_code == 0 and not self._result_read:
            with open(self.file_name, encoding="utf-8") as file:
                self.text_area.text = file.read()
            self.text_area.app.refresh()
            self._result_read = True
        elif message.exit_code != 0:
            self.text_area.app.notify(
                f"Neovim exited with status {message.exit_code}.", severity="error"
            )
        super().on_terminal_process_exited(message)

    def on_unmount(self) -> None:
        super().on_unmount()
        if os.path.exists(self.file_name):
            os.remove(self.file_name)


class RequestBodyTextArea(PostingTextArea):
    """
    For editing request bodies.
    """

    BINDING_GROUP_TITLE = "Request Body Text Area"

    BINDINGS = PostingTextArea.BINDINGS + [
        Binding("a", "open_in_editor", "Editor", show=False),
    ]

    help = HelpData(
        title="Request Body Text Area",
        description="""\
A text area for entering the request body.
Press `ESC` to focus the text area footer bar.
Press `ctrl+e` to edit the body in the Posting Neovim profile.

Hold `shift` and move the cursor or click and drag to select text.
""",
    )

    def on_mount(self):
        self.tab_behavior = "indent"
        self.show_line_numbers = True

    def action_open_in_editor(self) -> None:
        with tempfile.NamedTemporaryFile(
            suffix=f".{self.language}", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file_name = temp_file.name
            temp_file.write(self.text)

        self.app.mount(RequestBodyEditorWindow(self, temp_file_name))
