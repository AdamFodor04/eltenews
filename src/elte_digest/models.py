from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    url: str
    title: str
    published: str | None
    category: str | None
    text: str


@dataclass(frozen=True)
class Summary:
    article: Article
    text: str
