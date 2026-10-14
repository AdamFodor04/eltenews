import argparse
import logging

import requests

from .config import Settings
from .mailer import send_digest
from .models import Summary
from .scraper import discover_articles, load_article
from .store import Store
from .summarizer import summarize

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and email a daily ELTE TL;DR digest.")
    parser.add_argument("--seed", action="store_true", help="Record currently visible items without emailing them.")
    args = parser.parse_args()
    settings = Settings.from_environment()
    store = Store(settings.database_path)
    session = requests.Session()
    try:
        found = discover_articles(settings.index_urls, session)
        logging.info("Checked %d ELTE sections and discovered %d article/event links",
                     len(settings.index_urls), len(found))
        new_items = [item for item in found if not store.known(item.url)]
        if args.seed:
            for item in new_items:
                store.save(load_article(item, session))
            logging.info("Seeded %d items", len(new_items))
            return
        settings.validate_for_delivery()
        summaries = []
        for item in new_items:
            loaded = load_article(item, session)
            text = summarize(loaded, settings, session)
            store.save(loaded, text)
            summaries.append((loaded, text))
        digest = [Summary(article, text) for article, text in summaries]
        send_digest(digest, settings)
        store.mark_emailed([item.article.url for item in digest])
        logging.info("Emailed %d summaries", len(digest))
    finally:
        store.close()


if __name__ == "__main__":
    main()
