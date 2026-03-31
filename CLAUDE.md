# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YuriAudio2Notion extracts and syncs metadata from Yuri radio dramas (百合广播剧) on the Fanjiao platform into a Notion database. It runs as a FastAPI webhook server triggered by Notion button clicks.

## Commands

This project uses `uv` for dependency management (Python 3.11+ required).

```bash
# Install dependencies
uv sync

# Run the webhook server (development, with auto-reload)
python app/main.py

# Run the webhook server (production)
uvicorn app.main:app --host 0.0.0.0 --port 5050

# Run CLI batch processing (reads URLs from waiting_up_private.txt)
python cli.py

# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy .

# Docker
docker compose up -d
```

## Architecture

The app uses a layered architecture with one-way dependencies flowing upward:

```
Utils → Clients → Services → Core (Processor) → API (Routes)
```

**Two processing pipelines exist in parallel:**
- **Album pipeline**: `AlbumProcessor` → `FanjiaoService` + `NotionService` — handles radio drama albums
- **Audio pipeline**: `AudioProcessor` → `FanjiaoAudioService` + `NotionService` — handles individual audio tracks/songs

**Key flow for album processing:**
1. Notion button sends a POST webhook to `/webhook-data-source`
2. `routes.py` extracts `FanjiaoAlbumID` (number field) from the Notion page properties
3. `AlbumProcessor.process_id()` calls `FanjiaoService.fetch_album_data()`
4. `FanjiaoService` uses `FanjiaoAlbumClient` and `FanjiaoCVClient` to fetch data, then `description_parser.py` to extract tags/up主/episode counts from the description text
5. `NotionService.upload_album_data()` writes properties back to the Notion page via `NotionClient`

## Webhook Endpoints

| Endpoint | Trigger source | Notes |
|---|---|---|
| `POST /webhook-data-source` | Notion data source button | Main workflow; reads `FanjiaoAlbumID` number field |
| `POST /webhook-data-source-update` | Notion data source button | Partial update; reads `Update_selection` multi-select |
| `POST /webhook-page` | Notion page button | Reads URL from request header |
| `POST /webhook-url` | Direct HTTP call | Reads URL from request body |
| `POST /webhook-song` | Notion data source button | Audio track processing; reads `Audio_URL` url field |
| `POST /webhook-song-update` | Notion data source button | Partial audio update; reads `UpdateAudioSelection` multi-select |
| `POST /webhook-data-source-debug` | Any | Logs and echoes the full Notion payload |

All endpoints require the `YURI-API-KEY` header or `api_key` query param when `API_KEY` is set in env.

## Configuration

Copy `.env.template` to `.env`. All required env vars (except `API_KEY`) will raise `RuntimeError` at access time if missing — they are not validated at startup.

- `FANJIAO_SALT`, `FANJIAO_BASE_URL`, `FANJIAO_CV_BASE_URL`, `FANJIAO_AUDIO_BASE_URL` — Fanjiao API credentials
- `NOTION_TOKEN`, `NOTION_DATA_SOURCE_ID` — Notion integration token and default data source ID
- `API_KEY` — optional; if unset, all requests pass through with a warning log
- `ENV` — `development` enables uvicorn `reload=True`; `production` disables it
- `PORT` — defaults to `5050`

Config is a singleton at `app/utils/config.py:config`.

## Key Conventions

- **Notion field names** are defined as `StrEnum` constants in `app/constants/notion_fields.py` (`AlbumField`, `AudioField`). Always use these enums instead of hardcoded strings when referencing Notion properties.
- The `data_source_id` passed to `AlbumProcessor` overrides `NOTION_DATA_SOURCE_ID` from config, allowing the webhook to write to the database that triggered it (extracted from `request.data["parent"]["data_source_id"]`).
- `app/utils/cache.py` provides local file caching under `app/data_cache/` (mounted as a Docker volume).
- `cli.py` at the project root reads album URLs from `waiting_up_private.txt` (gitignored) for local batch processing.
- Scripts in `scripts/` (`inspect_data_source.py`, `inspect_page.py`) are standalone debugging utilities.
- `notion_button/simulate_button_click.py` can simulate a Notion button click locally for testing.
