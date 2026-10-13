import sqlite3
from pathlib import Path

from .models import Article


class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY, title TEXT NOT NULL, published TEXT, category TEXT,
            text TEXT NOT NULL, summary TEXT, discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            emailed_at TEXT
        )""")
        self.db.commit()

    def known(self, url: str) -> bool:
        return self.db.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone() is not None

    def save(self, article: Article, summary: str | None = None) -> None:
        self.db.execute(
            """INSERT OR REPLACE INTO articles(url,title,published,category,text,summary,discovered_at,emailed_at)
               VALUES(?,?,?,?,?,?,COALESCE((SELECT discovered_at FROM articles WHERE url = ?), CURRENT_TIMESTAMP),
                      (SELECT emailed_at FROM articles WHERE url = ?))""",
            (article.url, article.title, article.published, article.category, article.text, summary,
             article.url, article.url),
        )
        self.db.commit()

    def mark_emailed(self, urls: list[str]) -> None:
        self.db.executemany("UPDATE articles SET emailed_at = CURRENT_TIMESTAMP WHERE url = ?", [(url,) for url in urls])
        self.db.commit()

    def close(self) -> None:
        self.db.close()
