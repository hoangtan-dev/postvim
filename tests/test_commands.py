import asyncio

from posting.collection import RequestModel
from posting.commands import RequestSearchProvider


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
