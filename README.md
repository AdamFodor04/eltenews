# ELTE daily digest

This program checks [ELTE hírek és események](https://www.elte.hu/hirek-esemenyek) once per day, follows newly discovered article/event pages, creates concise Hungarian TL;DRs, and emails them. It stores URLs and summaries in SQLite so an item is not sent twice.

## Local setup

Requires Python 3.11+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install .
```

Set these environment variables:

* `OPENAI_API_KEY` and optional `OPENAI_MODEL` (the default is `gpt-4o-mini`; any OpenAI-compatible endpoint can be selected with `OPENAI_BASE_URL`)
* `SMTP_HOST`, optional `SMTP_PORT` (default `587`), `SMTP_USERNAME`, `SMTP_PASSWORD`
* `MAIL_FROM`, `MAIL_TO`
* optional `ELTE_DATABASE_PATH` and `ELTE_INDEX_URL`

On the first run, seed the existing index without sending an archive digest:

```powershell
elte-digest --seed
elte-digest
```

The normal command only emails links not already stored in `data/digest.db`. If fetching, summarization, or email delivery fails, it exits non-zero and leaves unemailed items in the database for the next run.

## Daily GitHub Actions run

The included workflow runs daily at 06:15 UTC and can also be started manually. Add the variables/secrets listed above in the repository settings. Run `elte-digest --seed` locally once and commit `data/digest.db` before enabling the schedule, or the first scheduled run will summarize every currently visible item.

The workflow commits the SQLite state after a successful run. For a private deployment, keep the repository private because the database contains copied article text and generated summaries.
