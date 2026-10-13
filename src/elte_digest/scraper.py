from collections.abc import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import Article

USER_AGENT = "elte-daily-digest/0.1 (+https://www.elte.hu/hirek-esemenyek)"


def _clean(value: str) -> str:
    return " ".join(value.split())


def _links(index_url: str, html: str) -> Iterable[tuple[str, str]]:
    root = urlparse(index_url)
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.select("a[href]"):
        href = urljoin(index_url, anchor["href"])
        href = urldefrag(href).url
        parsed = urlparse(href)
        text = _clean(anchor.get_text(" ", strip=True))
        if parsed.scheme in {"http", "https"} and parsed.netloc == root.netloc and text:
            yield href, text


def discover_articles(index_url: str, session: requests.Session | None = None) -> list[Article]:
    client = session or requests.Session()
    response = client.get(index_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    root_path = urlparse(index_url).path.rstrip("/")
    articles: dict[str, Article] = {}
    # ELTE has used several templates over time. The article-like containers and
    # links are intentionally detected by structure rather than brittle URL IDs.
    for container in soup.select("article, .news-item, .event-item, .list-item, .teaser, .card"):
        anchor = container.select_one("a[href]")
        if not anchor:
            continue
        url = urldefrag(urljoin(index_url, anchor["href"])).url
        parsed = urlparse(url)
        if parsed.netloc != urlparse(index_url).netloc or parsed.path.rstrip("/") == root_path:
            continue
        title = _clean((container.select_one("h1, h2, h3, h4, .title") or anchor).get_text(" ", strip=True))
        if len(title) < 8:
            continue
        date_node = container.select_one("time, .date, .published")
        category_node = container.select_one(".category, .type, .label")
        articles[url] = Article(url, title, date_node.get_text(" ", strip=True) if date_node else None,
                                category_node.get_text(" ", strip=True) if category_node else None, "")

    # Fallback for templates without semantic list containers: retain links that
    # look like content links, excluding navigation and the known landing page.
    if not articles:
        for url, text in _links(index_url, response.text):
            parsed = urlparse(url)
            if parsed.path.rstrip("/") == root_path or len(text) < 12:
                continue
            articles[url] = Article(url, text, None, None, "")
    return list(articles.values())


def load_article(article: Article, session: requests.Session | None = None) -> Article:
    client = session or requests.Session()
    response = client.get(article.url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for node in soup.select("script, style, nav, header, footer, noscript, form"):
        node.decompose()
    main = soup.select_one("main, article, .article, .content, .page-content") or soup.body
    text = _clean(main.get_text(" ", strip=True) if main else "")
    title_node = soup.select_one("h1, title")
    title = _clean(title_node.get_text(" ", strip=True)) if title_node else article.title
    return Article(article.url, title or article.title, article.published, article.category, text[:30000])
