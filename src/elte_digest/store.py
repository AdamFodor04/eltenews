import sqlite3
from pathlib import Path

from .models import Article, Summary


class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY, title TEXT NOT NULL, published TEXT, category TEXT,
            text TEXT NOT NULL, summary TEXT, discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            emailed_at TEXT, seeded_at TEXT
        )""")
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(articles)")}
        if "seeded_at" not in columns:
            self.db.execute("ALTER TABLE articles ADD COLUMN seeded_at TEXT")
        self.db.commit()

    def known(self, url: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM articles WHERE url = ? AND (emailed_at IS NOT NULL OR seeded_at IS NOT NULL)",
            (url,),
        ).fetchone() is not None

    def pending(self) -> list[Summary | Article]:
        rows = self.db.execute(
            """SELECT url, title, published, category, text, summary
               FROM articles
               WHERE emailed_at IS NULL AND seeded_at IS NULL
               ORDER BY discovered_at, url"""
        ).fetchall()
        result: list[Summary | Article] = []
        for url, title, published, category, text, summary in rows:
            article = Article(url, title, published, category, text)
            result.append(Summary(article, summary) if summary else article)
        return result

    def save(self, article: Article, summary: str | None = None, *, seeded: bool = False) -> None:
        self.db.execute(
            """INSERT OR REPLACE INTO articles(
                   url,title,published,category,text,summary,discovered_at,emailed_at,seeded_at
               )
               VALUES(
                   ?,?,?,?,?,?,
                   COALESCE((SELECT discovered_at FROM articles WHERE url = ?), CURRENT_TIMESTAMP),
                   (SELECT emailed_at FROM articles WHERE url = ?),
                   CASE WHEN ? THEN CURRENT_TIMESTAMP
                        ELSE (SELECT seeded_at FROM articles WHERE url = ?) END
               )""",
            (article.url, article.title, article.published, article.category, article.text, summary,
             article.url, article.url, seeded, article.url),
        )
        self.db.commit()

    def mark_emailed(self, urls: list[str]) -> None:
        self.db.executemany("UPDATE articles SET emailed_at = CURRENT_TIMESTAMP WHERE url = ?", [(url,) for url in urls])
        self.db.commit()

    def close(self) -> None:
        self.db.close()
