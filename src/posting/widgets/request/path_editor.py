from dataclasses import dataclass
from textual.binding import Binding
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message

from posting.collection import PathParam
from posting.widgets.datatable import PostingDataTable
from posting.widgets.key_value import KeyValueEditor
from posting.widgets.request.dict_editor import DictEditorWindow


class PathParamsTable(PostingDataTable):
    """
    Table of path parameters extracted from the URL.

    Rows are controlled by the URL. Users cannot add or remove rows manually.
    Press `a` to edit values in a floating Neovim window.
    """

    @dataclass
    class PathParamJumpRequestedFromPathParamsTable(Message):
        name: str
        editor_table: "PathParamsTable"

        @property
        def control(self) -> "PathParamsTable":
            return self.editor_table

    def on_mount(self):
        self.fixed_columns = 0
        self.show_header = False
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.row_disable = False
        self.add_columns("Key", "Value")

    BINDINGS = [
        *PostingDataTable.BINDINGS,
        Binding(
            "alt+down", "jump_to_url_param", "Jump to param in URL bar", show=False
        ),
        Binding("a", action="open_dict_editor", description="Edit path parameters", show=False),
    ]

    def action_open_dict_editor(self) -> None:
        editor = self.query_ancestor(PathParamsEditor)
        self.app.mount(DictEditorWindow(self, self.as_dict(), editor.apply_mapping, "Edit Path Parameters"))

    def as_dict(self) -> dict[str, str]:
        return {
            str(row[0].plain if isinstance(row[0], Text) else row[0]): str(
                row[1].plain if isinstance(row[1], Text) else row[1]
            )
            for row in (self.get_row_at(index) for index in range(self.row_count))
        }

    def action_remove_row(self) -> None:
        # Disallow manual row removal.
        return

    def action_jump_to_url_param(self) -> None:
        """Post a message requesting a jump to the corresponding param in the URL bar."""
        table = self
        row_index = table.cursor_row
        if row_index < 0 or row_index >= table.row_count:
            return
        row = table.get_row_at(row_index)
        key_cell = row[0]
        name = key_cell.plain if isinstance(key_cell, Text) else key_cell
        self.post_message(
            self.PathParamJumpRequestedFromPathParamsTable(
                name=str(name), editor_table=self
            )
        )

    def to_model(self) -> list[PathParam]:
        params: list[PathParam] = []
        for row_index in range(self.row_count):
            row = self.get_row_at(row_index)
            params.append(
                PathParam(
                    name=row[0].plain if isinstance(row[0], Text) else row[0],
                    value=(row[1].plain if isinstance(row[1], Text) else row[1]) or None,
                )
            )
        return params


class PathParamsEditor(KeyValueEditor):
    """
    Editor for path parameters. Users may edit keys and values, not add or remove rows.
    """

    @dataclass
    class PathParamsUpdated(Message):
        params: dict[str, str]

    @dataclass
    class PathParamRenamed(Message):
        old_name: str
        new_name: str

    def __init__(self) -> None:
        super().__init__(
            PathParamsTable(),
            None,
            empty_message=(
                "[b]No path parameters in URL[/]\n"
                "Use [$text-accent]:param[/] syntax to add them\n"
                "e.g. http://example.com/:foo/:bar"
            ),
        )

    def _get_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for row_index in range(self.table.row_count):
            row = self.table.get_row_at(row_index)
            key = row[0].plain if isinstance(row[0], Text) else row[0]
            val = row[1].plain if isinstance(row[1], Text) else row[1]
            params[str(key)] = str(val)
        return params

    def apply_mapping(self, values: dict[str, str | None]) -> None:
        params = {name: value or "" for name, value in values.items()}
        self.table.replace_all_rows(params.items(), [True] * len(params))
        self.post_message(self.PathParamsUpdated(params))


class PathEditor(Vertical):
    """
    The Path tab which contains the path parameter editor.
    """

    BINDINGS = [
        Binding("a", action="open_dict_editor", description="Edit path parameters", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield PathParamsEditor()

    def action_open_dict_editor(self) -> None:
        self.query_one(PathParamsTable).action_open_dict_editor()
