from textual.binding import Binding

from posting.widgets.response.response_body import ResponseTextArea
from posting.widgets.datatable import PostingDataTable


class ResponseHeadersTable(PostingDataTable):
    BINDINGS = PostingDataTable.BINDINGS + [
        Binding("slash", "open_response_in_pager", "Pager", show=False),
    ]

    def on_mount(self) -> None:
        self.show_header = False
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.fixed_columns = 1
        self.add_columns(*["Header", "Value"])
        self.cursor_vertical_escape = False

    def action_open_response_in_pager(self) -> None:
        """Open the loaded response body without changing focus or tabs."""
        self.screen.query_one(ResponseTextArea).action_open_in_pager()
