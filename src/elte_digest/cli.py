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
                store.save(load_article(item, session), seeded=True)
            logging.info("Seeded %d items", len(new_items))
            return
        summaries = []
        pending_urls = set()
        for pending in store.pending():
            pending_urls.add(pending.article.url if isinstance(pending, Summary) else pending.url)
            if isinstance(pending, Summary):
                summaries.append((pending.article, pending.text))
            else:
                text = summarize(pending, settings, session)
                store.save(pending, text)
                summaries.append((pending, text))
        for item in new_items:
            if item.url in pending_urls:
                continue
            loaded = load_article(item, session)
            text = summarize(loaded, settings, session)
            store.save(loaded, text)
            summaries.append((loaded, text))
        digest = [Summary(article, text) for article, text in summaries]
        if not digest:
            logging.info("No new summaries to email")
            return
        settings.validate_for_delivery()
        send_digest(digest, settings)
        store.mark_emailed([item.article.url for item in digest])
        logging.info("Emailed %d summaries", len(digest))
    finally:
        store.close()


if __name__ == "__main__":
    main()
