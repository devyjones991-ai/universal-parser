import httpx
import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser import UniversalParser, parse_catalog_html


@pytest.mark.asyncio
async def test_scrape_public_catalog_with_mock_transport():
    html = """
    <div class='card'>
        <span class='title'>Компания</span>
        <a class='link' href='https://example.com'>Сайт</a>
    </div>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport, base_url="https://mock") as client:
        parser = UniversalParser()
        parser.session = client
        results = await parser.scrape_public_catalog(
            "https://mock/catalog",
            item_selector="div.card",
            field_selectors={"name": "span.title", "website": "a.link"},
            attributes={"website": "href"},
        )

    assert results == [{"name": "Компания", "website": "https://example.com"}]


def test_parse_catalog_html_extracts_fields():
    html = """
    <section>
        <article class='entry'>
            <h2>Товар 1</h2>
            <span class='price'>100</span>
        </article>
        <article class='entry'>
            <h2>Товар 2</h2>
            <span class='price'>200</span>
        </article>
    </section>
    """
    items = parse_catalog_html(
        html,
        item_selector="article.entry",
        field_selectors={"title": "h2", "price": "span.price"},
    )
    assert items == [
        {"title": "Товар 1", "price": "100"},
        {"title": "Товар 2", "price": "200"},
    ]
