from functools import partial
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.content import Content
from textual.screen import Screen
from textual.types import IgnoreReturnCallbackType
from posting.collection import RequestModel
from posting.widgets.load_env_file_dialog import show_load_env_file_dialog

if TYPE_CHECKING:
    from posting.app import Posting


CommandType = tuple[str, IgnoreReturnCallbackType, str, bool]


class RequestSearchProvider(Provider):
    """Search requests by their identifying metadata."""

    def __init__(
        self,
        screen: Screen[Any],
        requests: Sequence[tuple[RequestModel, str, Callable[[], None]]],
        match_style=None,
    ) -> None:
        super().__init__(screen, match_style)
        self.requests = requests

    @staticmethod
    def _search_fields(request: RequestModel, path: str) -> tuple[str, ...]:
        url_path = urlsplit(request.url).path or request.url
        parameter_names = [
            parameter.name for parameter in (*request.path_params, *request.params)
        ]
        return (
            request.name,
            path,
            str(request.method),
            url_path,
            request.description,
            " ".join(parameter_names),
        )

    async def search(self, query: str) -> Hits:
        tokens = query.split()
        if not tokens:
            return

        results = []
        for request, path, callback in self.requests:
            fields = self._search_fields(request, path)
            token_matchers = [self.matcher(token) for token in tokens]
            token_scores = []
            name_scores = []
            url_scores = []
            name = request.name
            highlighted_name = Content.from_markup(name)

            for matcher in token_matchers:
                name_score = matcher.match(name)
                url_score = max(matcher.match(fields[1]), matcher.match(fields[3]))
                field_score = max(
                    (matcher.match(field) for field in fields if field),
                    default=0,
                )
                if field_score == 0:
                    break
                token_scores.append(field_score)
                name_scores.append(name_score)
                url_scores.append(url_score)

                _, offsets = matcher.fuzzy_search.match(matcher.query, name)
                if name_score > 0:
                    for offset in offsets:
                        if not name[offset].isspace():
                            highlighted_name = highlighted_name.stylize(
                                matcher.match_style,
                                offset,
                                offset + 1,
                            )
            else:
                score = sum(
                    field_score + (2 * name_score) + url_score
                    for field_score, name_score, url_score in zip(
                        token_scores, name_scores, url_scores
                    )
                ) / len(token_scores)
                results.append(
                    Hit(
                        score,
                        highlighted_name,
                        callback,
                        text=request.name,
                        help=path,
                    )
                )

        for hit in sorted(results, key=lambda hit: hit.score, reverse=True):
            yield hit

    async def discover(self) -> Hits:
        for request, path, callback in self.requests:
            yield DiscoveryHit(request.name, callback, help=path)


def make_request_search_provider(
    requests: Sequence[tuple[RequestModel, str, Callable[[], None]]],
) -> type[RequestSearchProvider]:
    """Bind request data to a provider class for CommandPalette."""

    class BoundRequestSearchProvider(RequestSearchProvider):
        def __init__(self, screen, match_style=None) -> None:
            super().__init__(screen, requests, match_style)

    return BoundRequestSearchProvider


class PostingProvider(Provider):
    @property
    def commands(
        self,
    ) -> tuple[tuple[str, IgnoreReturnCallbackType, str, bool], ...]:
        app = self.posting
        screen = self.screen

        commands_to_show: list[tuple[str, IgnoreReturnCallbackType, str, bool]] = []

        from posting.app import MainScreen

        if isinstance(screen, MainScreen):
            # Only show the option to change to the layout which isn't the current one.
            if screen.current_layout == "horizontal":
                commands_to_show.append(
                    (
                        "layout: Vertical",
                        partial(app.command_layout, "vertical"),
                        "Change layout to vertical",
                        True,
                    ),
                )
            elif screen.current_layout == "vertical":
                commands_to_show.append(
                    (
                        "layout: Horizontal",
                        partial(app.command_layout, "horizontal"),
                        "Change layout to horizontal",
                        True,
                    ),
                )

            if screen.url_bar.url_input.value.strip() != "":
                commands_to_show.append(
                    (
                        "export: copy as curl",
                        app.command_export_to_curl,
                        "Copy the request as a curl command",
                        True,
                    ),
                )

                commands_to_show.append(
                    (
                        "export: copy as curl (no setup scripts)",
                        partial(app.command_export_to_curl, run_setup_scripts=False),
                        "Copy the request as a curl command without setup scripts",
                        True,
                    ),
                )

                # Copy current request YAML (reflecting unsaved UI state)
                commands_to_show.append(
                    (
                        "export: copy as YAML",
                        app.command_copy_request_yaml,
                        "Copy the current request YAML to the clipboard",
                        True,
                    ),
                )
            # Change the available commands depending on what is currently
            # maximized on the main screen.
            expand_section_callback: IgnoreReturnCallbackType = partial[None](
                screen.expand_section, None
            )
            reset_command: CommandType = (
                "view: Reset",
                expand_section_callback,
                "Reset the size of the request & response sections",
                True,
            )
            expand_request_callback: IgnoreReturnCallbackType = partial[None](
                screen.expand_section, "request"
            )
            expand_request_command: CommandType = (
                "view: Expand request section",
                expand_request_callback,
                "Expand the request section and hide the response section",
                True,
            )
            expand_response_callback: IgnoreReturnCallbackType = partial[None](
                screen.expand_section, "response"
            )
            expand_response_command: CommandType = (
                "view: Expand response section",
                expand_response_callback,
                "Expand the response section and hide the request section",
                True,
            )
            expanded_section = screen.expanded_section
            if expanded_section == "request":
                commands_to_show.extend([reset_command, expand_response_command])
            elif expanded_section == "response":
                commands_to_show.extend([reset_command, expand_request_command])
            else:
                commands_to_show.extend(
                    [expand_request_command, expand_response_command]
                )

            toggle_collection_browser_callback: IgnoreReturnCallbackType = partial[
                None
            ](screen.action_toggle_collection_browser)
            toggle_collection_browser_command: CommandType = (
                "view: Toggle collection browser",
                toggle_collection_browser_callback,
                "Toggle the collection browser sidebar",
                True,
            )
            commands_to_show.append(toggle_collection_browser_command)

            toggle_spacing_callback: IgnoreReturnCallbackType = partial[None](
                app.command_toggle_spacing
            )
            title = (
                "spacing: Enable compact mode"
                if app.spacing == "standard"
                else "spacing: Enable standard mode"
            )
            help_text = (
                "Reduce user interface spacing"
                if app.spacing == "standard"
                else "Increase user interface spacing"
            )
            toggle_spacing_command: CommandType = (
                title,
                toggle_spacing_callback,
                help_text,
                True,
            )
            commands_to_show.append(toggle_spacing_command)

        # Global commands, not specific to the MainScreen.
        if not app.ansi_color:
            commands_to_show.append(
                (
                    "theme: Preview theme",
                    app.action_change_theme,
                    "Preview a theme for the current session",
                    True,
                ),
            )

            commands_to_show.append(
                (
                    "environment: Load env file",
                    lambda: show_load_env_file_dialog(app),
                    "Load environment variables from a .env file",
                    True,
                ),
            )

        if screen.query("HelpPanel"):
            commands_to_show.append(
                (
                    "help: Hide keybindings sidebar",
                    app.action_hide_help_panel,
                    "Hide the keybindings sidebar",
                    True,
                ),
            )
        else:
            commands_to_show.append(
                (
                    "help: Show keybindings sidebar",
                    app.action_show_help_panel,
                    "Display keybindings for the focused widget in a sidebar",
                    True,
                ),
            )

        commands_to_show.append(
            (
                "help: Open web docs",
                app.action_open_web_docs,
                "Open the web docs in the default browser",
                True,
            ),
        )
        commands_to_show.append(
            (
                "app: Quit Posting",
                app.action_quit,
                "Quit Posting and return to the command line",
                True,
            ),
        )

        return tuple(commands_to_show)

    async def discover(self) -> Hits:
        """Handle a request for the discovery commands for this provider.

        Yields:
            Commands that can be discovered.
        """
        for name, runnable, help_text, show_discovery in self.commands:
            if show_discovery:
                yield DiscoveryHit(
                    name,
                    runnable,
                    help=help_text,
                )

    async def search(self, query: str) -> Hits:
        """Handle a request to search for commands that match the query.

        Args:
            query: The user input to be matched.

        Yields:
            Command hits for use in the command palette.
        """
        matcher = self.matcher(query)
        for name, runnable, help_text, _ in self.commands:
            if (match := matcher.match(name)) > 0:
                yield Hit(
                    match,
                    matcher.highlight(name),
                    runnable,
                    help=help_text,
                )

    @property
    def posting(self) -> "Posting":
        return cast("Posting", self.screen.app)
