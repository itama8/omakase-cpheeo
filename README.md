# omakase-cpheeo

Search and cite the CPHEEO manuals (Government of India) over MCP and REST. Every result carries the manual, edition, part, clause or table, and printed page, with Omakase attribution.

Indexed now: Manual on Sewerage and Sewage Treatment Systems, Part A: Engineering (2013), including all 51 source-listed appendices/sheets, and Manual on Water Supply and Treatment Systems, Parts A, B and C (2024). Storm water (2019) and solid waste (2016) are next. See `docs/plan.md`.

## Requirements

- Python 3.13 and [uv](https://docs.astral.sh/uv/)
- The source PDFs in a local folder (not in this repo). Default `~/Downloads/CPHEEO`; override with `OMAKASE_CPHEEO_SOURCES`.

## Use

```sh
uv run omakase-cpheeo ingest                 # parse the manuals, build data/build/cpheeo.sqlite (all four source manuals)
uv run omakase-cpheeo search minimum slope for 200 mm sewer
uv run python scripts/visual_coverage.py     # page review and transcription coverage
uv run python scripts/check_verified_retrieval.py  # numerical/formula retrieval and provenance
uv run omakase-cpheeo clause SEW-2013-A:T3.2
uv run omakase-cpheeo eval -v                # score retrieval against eval/questions.yaml
uv run omakase-cpheeo eval --questions eval/search-ranking.yaml -k 1 -v  # diameter ranking regressions
uv run omakase-cpheeo serve --port 8765      # MCP at /mcp, REST at /v1/*
uv run omakase-cpheeo eval --questions eval/sewage-appendices.yaml -v  # appendix retrieval
uv run python scripts/check_appendix_coverage.py  # compare all appendix pages with source contents
uv run python scripts/mcp_smoke.py           # exercise every MCP tool against a running server
```

## Interface

MCP tools (streamable HTTP at `/mcp`): `search`, `fetch`, `get_clause`, `get_toc`, `list_manuals`. `search` and `fetch` follow the result and document shape ChatGPT connectors use.

REST:

| Endpoint | Returns |
|---|---|
| `GET /v1/search?q=...&domain=&manual=&kind=&limit=` | Ranked units with citation and snippet |
| `GET /v1/clause/{id}?children=1` | Section text, native table rows and source-image references |
| `GET /v1/manuals` | Manuals and unit counts |
| `GET /v1/toc/{manual}?chapter=3` | Chapters, sections and tables |
| `GET /c/{id}` | Readable clause page with Omakase attribution (what result `url`s point to) |
| `GET /img/{id}/{seq}.png` (or `.jpg`) | Source-page image for a table, figure or scanned content |
| `GET /health` | Liveness and loaded manuals |

Unit ids are citation handles: `SEW-2013-A:3.6` (section), `SEW-2013-A:T3.2` (table), `SEW-2013-A:F3.4` (figure), `WS-2024-A:AN6.1` (annexure), `WS-2024-A:AN6.3-T4` (Table 4 inside Annexure 6.3; annexures number their tables from 1).

Sewage Parts B (Operation and Maintenance) and C (Management) are deferred until their published source PDFs are available locally.

The sewage appendices have separate handles such as `SEW-2013-A:A3.2B` (lettered sheet), `SEW-2013-A:TA7.3-1` (appendix table) and `SEW-2013-A:FA3.2A-1` (appendix figure). The old grouped handles (`A3.2`, `A3.4`, `A3.5`) still return both sheets. Appendix titles and page boundaries come from the manual's native-text contents, and all 185 appendix pages are available as full-page images. Lookup accepts printed references such as "Appendix A 3.2 B" or "Table A 7.3- 1".

Scanned tables and figures retain source imagery. Visually transcribed and separately rechecked text is available where explicitly marked `transcription_status: verified`: cells under `verified_transcriptions[].rows`, searchable text under `verified_text`, and LaTeX/readable representations for equations. Original images remain available alongside exact source-region crops, PDF hashes and verification observations. Equation handles include `SEW-2013-A:E5.30` and also appear on their parent sections.

**Visual transcription proceeds in small targeted batches.** There are 295 verified records (136 tables, 159 equations) and one unclear formula. Select a few known tables/equations from the inventory or retrieval needs, inspect their source crops and necessary continuations, and verify those records. An exhaustive page sweep is not required. The historical page ledger is audit metadata, not a queue of thousands of pages to inspect. See [visual transcription coverage and workflow](docs/visual-transcriptions.md). No OCR is run. Native water table text is not automatically visually verified; unclear math retains its source image and explicit note.

Verified values, table headers, notes and mathematical text are searchable. `get_clause` and `fetch` include the text, provenance and MCP image blocks; REST returns the same data and image references; clause pages display text and source images. Verify the returned record's scope and any source-error notes before interpreting numerical values.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `OMAKASE_CPHEEO_SOURCES` | `~/Downloads/CPHEEO` | Folder holding the source PDFs |
| `OMAKASE_CPHEEO_DB` | `data/build/cpheeo.sqlite` | Index used by the server |
| `OMAKASE_CPHEEO_BRAND_URL` | unset | Link included in every result's attribution |
| `OMAKASE_CPHEEO_PUBLIC_URL` | unset | Public base URL (tunnel or deployment); adds result links and allows that Host |
| `OMAKASE_CPHEEO_ALLOWED_ORIGINS` | unset | Extra comma-separated browser origins to accept |
| `OMAKASE_CPHEEO_TABLE_IMAGE_DPI` | `200` | PNG resolution for scanned tables and other embedded pictures |
| `OMAKASE_CPHEEO_FIGURE_IMAGE_DPI` | `130` | JPEG resolution for full figure pages |

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
