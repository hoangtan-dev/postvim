import asyncio

from posting.collection import RequestModel
from posting.commands import EnvironmentSearchProvider, RequestSearchProvider


def request(name: str, url: str) -> RequestModel:
    return RequestModel(name=name, method="GET", url=url)


def test_request_search_matches_tokens_in_any_order():
    provider = RequestSearchProvider(
        None,
        [(request("Search consumers", "https://example.com/consumers/search"), "", lambda: None)],
    )

    async def collect():
        return [hit async for hit in provider.search("consumers search")]

    hits = asyncio.run(collect())

    assert len(hits) == 1
    assert hits[0].text == "Search consumers"


def test_request_search_requires_every_token():
    provider = RequestSearchProvider(
        None,
        [(request("Search consumers", "https://example.com/consumers/search"), "", lambda: None)],
    )

    async def collect():
        return [hit async for hit in provider.search("consumers missing")]

    hits = asyncio.run(collect())

    assert hits == []


def test_environment_search_lists_files_and_matches_name(tmp_path):
    local = tmp_path / "env.local"
    ci = tmp_path / "env.ci"
    provider = EnvironmentSearchProvider(
        None,
        [
            (local, "posting/envs/env.local", lambda: None),
            (ci, "posting/envs/env.ci", lambda: None),
        ],
    )

    async def collect(query: str):
        return [hit async for hit in provider.search(query)]

    all_hits = asyncio.run(collect(""))
    ci_hits = asyncio.run(collect("ci"))

    assert [hit.text for hit in all_hits] == ["env.ci", "env.local"]
    assert [hit.text for hit in ci_hits] == ["env.ci"]
