from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from posting.collection import Header
from posting.help_data import HelpData

from posting.widgets.datatable import PostingDataTable
from posting.widgets.key_value import KeyValueEditor
from posting.widgets.request.dict_editor import DictEditorWindow


HEADER_SUGGESTIONS = {
    "accept": [
        # Common prefixes for autocompletion
        "application/",
        "audio/",
        "font/",
        "image/",
        "text/",
        "video/",
        "multipart/",
        # Common wildcards
        "*",
        "*/*",
        "image/*",
        "audio/*",
        "video/*",
        # Application types
        "application/json",
        "application/xml",
        "application/x-www-form-urlencoded",
        "application/javascript",
        "application/pdf",
        "application/zip",
        "application/octet-stream",
        "application/graphql",
        "application/msgpack",
        # Text types
        "text/plain",
        "text/html",
        "text/css",
        "text/csv",
        "text/markdown",
        "text/yaml",
    ],
    "accept-encoding": [
        # Single encodings
        "gzip",
        "deflate",
        "br",
        "compress",
        "identity",
        "*",
        # Common combinations
        "gzip, deflate",
        "gzip, deflate, br",
    ],
    "accept-language": [
        # Common single languages
        "en",
        "en-US",
        "en-GB",
        "es",
        "es-ES",
        "fr",
        "fr-FR",
        "de",
        "de-DE",
        "it",
        "ja",
        "ko",
        "zh",
        "zh-CN",
        "zh-TW",
        "*",
    ],
    "authorization": [
        # Auth scheme prefixes
        "Bearer ",
        "Basic ",
        "Digest ",
        "OAuth ",
        "JWT ",
        "ApiKey ",
    ],
    "cache-control": [
        # Single directives
        "no-cache",
        "no-store",
        "no-transform",
        "private",
        "public",
        "must-revalidate",
        "proxy-revalidate",
        "max-age=0",
        # Common combinations
        "no-cache, no-store",
        "private, no-cache",
        "no-cache, must-revalidate",
        # Time-based examples
        "max-age=3600",
        "max-age=86400",
        "max-age=604800",
    ],
    "connection": [
        "keep-alive",
        "close",
        "upgrade",
    ],
    "content-type": [
        # Common prefixes for autocompletion
        "application/",
        "audio/",
        "font/",
        "image/",
        "text/",
        "video/",
        "multipart/",
        # Application types
        "application/json",
        "application/xml",
        "application/x-www-form-urlencoded",
        "application/javascript",
        "application/pdf",
        "application/zip",
        "application/octet-stream",
        "application/graphql",
        "application/msgpack",
        # Text types
        "text/plain",
        "text/html",
        "text/css",
        "text/csv",
        "text/markdown",
        "text/yaml",
        # Multipart types
        "multipart/form-data",
        "multipart/mixed",
        "multipart/alternative",
        # Image types
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "image/avif",
        # Audio types
        "audio/mpeg",
        "audio/ogg",
        "audio/wav",
        # Video types
        "video/mp4",
        "video/webm",
        "video/ogg",
    ],
    "if-match": [
        "*",
        "W/",  # Weak validator prefix
    ],
    "if-none-match": [
        "*",
        "W/",  # Weak validator prefix
    ],
    "pragma": [
        "no-cache",
    ],
    "range": [
        # Common range patterns
        "bytes=",
        "bytes=0-",
        "bytes=0-499",
        "bytes=-500",
        "bytes=500-999",
        "bytes=0-499,500-999",
    ],
}


class HeaderEditor(Vertical):
    BINDING_GROUP_TITLE = "HTTP Header Editor"
    BINDINGS = [
        Binding("a", action="open_dict_editor", description="Edit headers", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield KeyValueEditor(
            HeadersTable(),
            None,
            empty_message="No headers",
        )

    def action_open_dict_editor(self) -> None:
        self.query_one(HeadersTable).action_open_dict_editor()

class HeadersTable(PostingDataTable):
    """
    The headers table.
    """

    help = HelpData(
        title="Headers Table",
        description="""\
A table of HTTP headers that will be sent with the request.
Press `a` to edit all headers in a floating Neovim window.
Press `backspace` to delete a header.
Press `space` to toggle a header on and off.
Posting will automatically attach a `User-Agent` header to outgoing requests in order to identify itself, and set the `Content-Type` depending on the content
in the body tab. Setting a header in this table will override the default value in these cases.
""",
    )

    BINDING_GROUP_TITLE = "Headers Table"

    BINDINGS = [
        Binding("backspace", action="remove_row", description="Remove header"),
        Binding("a", action="open_dict_editor", description="Edit headers", show=False),
    ]

    def on_mount(self):
        self.show_header = False
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.fixed_columns = 1
        self.row_disable = True
        self.add_columns(*["Header", "Value"])

    def action_open_dict_editor(self) -> None:
        self.app.mount(
            DictEditorWindow(self, self.as_dict(), self.apply_mapping, "Edit Headers")
        )

    def apply_mapping(self, values: dict[str, str | None]) -> None:
        rows = [(name, value or "") for name, value in values.items()]
        self.replace_all_rows(rows, [value is not None for value in values.values()])

    def watch_has_focus(self, value: bool) -> None:
        self._scroll_cursor_into_view()
        return super().watch_has_focus(value)

    def as_dict(self) -> dict[str, str | None]:
        headers: dict[str, str | None] = {}
        for row_index in range(self.row_count):
            row = self.get_row_at(row_index)
            name = row[0].plain if isinstance(row[0], Text) else row[0]
            value = row[1].plain if isinstance(row[1], Text) else row[1]
            headers[str(name)] = str(value) if self.is_row_enabled_at(row_index) else None
        return headers

    def to_model(self) -> list[Header]:
        headers: list[Header] = []
        for row_index in range(self.row_count):
            row = self.get_row_at(row_index)
            plain_row0 = row[0].plain if isinstance(row[0], Text) else row[0]
            plain_row1 = row[1].plain if isinstance(row[1], Text) else row[1]
            is_row_enabled = self.is_row_enabled_at(row_index)
            headers.append(
                Header(
                    name=plain_row0,
                    value=plain_row1 if is_row_enabled else None,
                    enabled=is_row_enabled,
                )
            )
        return headers
