import json
import time
import requests

from .config import Settings
from .models import Article


def summarize(article: Article, settings: Settings, session: requests.Session | None = None) -> str:
    if not article.text:
        raise RuntimeError(f"Article has no readable text: {article.url}")
    payload = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You write concise, factual Hungarian TL;DRs. Never invent facts."},
            {"role": "user", "content": (
                "Summarize this ELTE news/event in 2-4 bullet points in Hungarian. "
                "Include who/what, date or deadline, location, and a useful link context when present. "
                f"Title: {article.title}\nText:\n{article.text}"
            )},
        ],
    }
    client = session or requests.Session()
    for attempt in range(3):
        response = client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
            data=json.dumps(payload), timeout=90,
        )
        if response.status_code != 429 or attempt == 2:
            break
        retry_after = response.headers.get("Retry-After")
        try:
            delay = min(float(retry_after), 60) if retry_after else 2 ** attempt
        except ValueError:
            delay = 2 ** attempt
        time.sleep(delay)
    if response.status_code == 429:
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(
            "OpenAI rate limit/quota exceeded after 3 attempts. "
            "Check the API account billing and limits. "
            f"Response: {detail}"
        )
    response.raise_for_status()
    try:
        content = response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Summarizer returned an invalid response") from exc
    if not content:
        raise RuntimeError(f"Summarizer returned an empty summary for {article.url}")
    return content
