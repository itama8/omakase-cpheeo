# omakase-cpheeo

Search and cite the CPHEEO manuals (Government of India) over MCP and REST. Every result carries the manual, edition, part, clause or table, and printed page, with Omakase attribution.

Indexed now: Manual on Sewerage and Sewage Treatment Systems, Part A: Engineering (2013), and Manual on Water Supply and Treatment Systems, Parts A, B and C (2024). Storm water (2019) and solid waste (2016) are next. See `docs/plan.md`.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- Tesseract with English data (`tesseract --list-langs` shows `eng`), for tables that are images in the PDFs
- The source PDFs in a local folder (not in this repo). Default `~/Downloads/CPHEEO`; override with `OMAKASE_CPHEEO_SOURCES`.

## Use

```sh
uv run omakase-cpheeo ingest                 # parse the manuals, build data/build/cpheeo.sqlite (~5 min for all four)
uv run omakase-cpheeo search minimum slope for 200 mm sewer
uv run omakase-cpheeo clause SEW-2013-A:T3.2
uv run omakase-cpheeo eval -v                # score retrieval against eval/questions.yaml
uv run omakase-cpheeo serve --port 8765      # MCP at /mcp, REST at /v1/*
uv run python scripts/mcp_smoke.py           # exercise every MCP tool against a running server
```

## Interface

MCP tools (streamable HTTP at `/mcp`): `search`, `fetch`, `get_clause`, `get_toc`, `list_manuals`. `search` and `fetch` follow the result and document shape ChatGPT connectors use.

REST:

| Endpoint | Returns |
|---|---|
| `GET /v1/search?q=...&domain=&manual=&kind=&limit=` | Ranked units with citation and snippet |
| `GET /v1/clause/{id}?children=1` | Full section text or table rows, with tables under that section |
| `GET /v1/manuals` | Manuals and unit counts |
| `GET /v1/toc/{manual}?chapter=3` | Chapters, sections and tables |
| `GET /c/{id}` | Readable clause page with Omakase attribution (what result `url`s point to) |
| `GET /health` | Liveness and loaded manuals |

Unit ids are citation handles: `SEW-2013-A:3.6` (section), `SEW-2013-A:T3.2` (table), `SEW-2013-A:F3.4` (figure), `WS-2024-A:AN6.1` (annexure), `WS-2024-A:AN6.3-T4` (Table 4 inside Annexure 6.3; annexures number their tables from 1).

Sewerage tables are images and are read by OCR (`source`: OCR). Water manual tables are text in the PDF and are read from the ruled grid (`source`: table text). Tables marked `needs_review` were OCR'd with doubts, or had no readable table under the caption; `data/build/review.json` lists them with the reason.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `OMAKASE_CPHEEO_SOURCES` | `~/Downloads/CPHEEO` | Folder holding the source PDFs |
| `OMAKASE_CPHEEO_DB` | `data/build/cpheeo.sqlite` | Index used by the server |
| `OMAKASE_CPHEEO_BRAND_URL` | unset | Link included in every result's attribution |
| `OMAKASE_CPHEEO_PUBLIC_URL` | unset | Public base URL (tunnel or deployment); adds result links and allows that Host |
| `OMAKASE_CPHEEO_ALLOWED_ORIGINS` | unset | Extra comma-separated browser origins to accept |
| `OMAKASE_CPHEEO_TABLE_DPI` | `300` | Render resolution for table OCR |

## Branding

Assistants often skip server instructions, so the Omakase brand travels in the data they copy:

- Every result's `citation` ends with ` · via Omakase CPHEEO`. `citation_plain` is the same reference without the suffix, for pasting into reports.
- Every result carries `source_name: "Omakase CPHEEO"`, and `source_icon` (the icon URL) when `OMAKASE_CPHEEO_PUBLIC_URL` is set.
- `fetch` titles start with `Omakase CPHEEO · `. `fetch` text and `get_clause` (`source_note`, its first field) carry one line: `Source: Omakase CPHEEO search (free CPHEEO lookup by Omakase)`, plus the clause page URL when a public URL is set.
- The MCP server is named "Omakase CPHEEO" (title "Omakase CPHEEO: search and cite CPHEEO manuals") and declares the Omakase icon: `<public URL>/icon.png`, or an inline `data:` PNG without a public URL. Tool titles start with "Omakase CPHEEO:".
- `/icon.png` (256 px), `/icon-1024.png` and `/favicon.ico` serve the icon (`assets/`, from the Omakase app icon). Clause pages show it next to "Omakase CPHEEO".

When adding the connector in ChatGPT or Claude, name it "Omakase CPHEEO", and upload `assets/omakase-icon.png` as its icon if the form allows one.

The manuals are Government of India copyright and may not be reproduced for commercial purposes without MoHUA permission. The free service returns cited excerpts; it does not redistribute the PDFs.

## Test from ChatGPT or Claude (temporary public URL)

```sh
mise exec cloudflared@latest -- cloudflared tunnel --url http://127.0.0.1:8765   # prints https://<random>.trycloudflare.com
OMAKASE_CPHEEO_PUBLIC_URL=https://<random>.trycloudflare.com uv run omakase-cpheeo serve
```

Add `https://<random>.trycloudflare.com/mcp` as a custom MCP connector with no authentication. The URL changes every time the tunnel restarts.
