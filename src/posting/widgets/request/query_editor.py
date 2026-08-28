from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from posting.collection import QueryParam

from posting.widgets.datatable import PostingDataTable
from posting.widgets.key_value import KeyValueEditor
from posting.widgets.request.dict_editor import DictEditorWindow


class ParamsTable(PostingDataTable):
    """
    The parameters table.
    """

    BINDINGS = [
        *PostingDataTable.BINDINGS,
        Binding("backspace", action="remove_row", description="Remove row"),
        Binding("a", action="open_dict_editor", description="Edit query parameters", show=False),
    ]

    def on_mount(self):
        self.fixed_columns = 1
        self.show_header = False
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.row_disable = True
        self.add_columns("Key", "Value")

    def action_open_dict_editor(self) -> None:
        self.app.mount(DictEditorWindow(self, self.as_dict(), self.apply_mapping, "Edit Query Parameters"))

    def as_dict(self) -> dict[str, str | None]:
        params: dict[str, str | None] = {}
        for index in range(self.row_count):
            row = self.get_row_at(index)
            name = row[0].plain if isinstance(row[0], Text) else row[0]
            value = row[1].plain if isinstance(row[1], Text) else row[1]
            params[str(name)] = str(value) if self.is_row_enabled_at(index) else None
        return params

    def apply_mapping(self, values: dict[str, str | None]) -> None:
        rows = [(name, value or "") for name, value in values.items()]
        self.replace_all_rows(rows, [value is not None for value in values.values()])

    def watch_has_focus(self, value: bool) -> None:
        self._scroll_cursor_into_view()
        return super().watch_has_focus(value)

    def to_model(self) -> list[QueryParam]:
        params: list[QueryParam] = []
        for row_index in range(self.row_count):
            row = self.get_row_at(row_index)
            params.append(
                QueryParam(
                    name=row[0].plain if isinstance(row[0], Text) else row[0],
                    value=(
                        row[1].plain if isinstance(row[1], Text) else row[1]
                    )
                    if self.is_row_enabled_at(row_index)
                    else None,
                    enabled=self.is_row_enabled_at(row_index),
                )
            )
        return params


class QueryStringEditor(Vertical):
    """
    The query string editor.
    """

    BINDINGS = [
        Binding("a", action="open_dict_editor", description="Edit query parameters", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield KeyValueEditor(
            ParamsTable(),
            None,
            empty_message="No query parameters",
        )

    @property
    def query_table(self) -> ParamsTable:
        return self.query_one(ParamsTable)

    def action_open_dict_editor(self) -> None:
        self.query_table.action_open_dict_editor()
