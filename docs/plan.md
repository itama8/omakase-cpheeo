# omakase-cpheeo plan

## Goal

A free, Omakase-branded service that lets engineers and their agents (Claude, ChatGPT, scripts) search the CPHEEO manuals and cite them exactly: manual, edition, part, clause or table, printed page. It is the top of the funnel for Omakase's paid civil and environmental offerings.

## Corpus

Latest parseable edition per domain. Source PDFs stay outside the repo (`OMAKASE_CPHEEO_SOURCES`, default `~/Downloads/CPHEEO`).

| Id | Manual | Status |
|---|---|---|
| `SEW-2013-A` | Sewerage and Sewage Treatment Systems, Part A: Engineering, 2013 (third edition) | Indexed |
| `WS-2024-A/B/C` | Water Supply and Treatment Systems, Parts A, B, C, March 2024 (fourth edition) | Next |
| `SWD-2019-A`, `SWD-2019-BC` | Storm Water Drainage, Vol I Part A and Vol II Parts B/C, August 2019 | Planned |
| `MSW-2016` | Municipal Solid Waste Management, Parts 1-3, 2016 | Planned |

Excluded: superseded editions (1999 water supply, the May 2012 sewerage draft), commercial textbooks in the source folder (Metcalf & Eddy, the calculation manual), advisories and SOPs (phase 2).

## Licensing

The manuals are Government of India copyright: "No portion, part or whole, of this document may be reproduced/printed for any type of commercial purposes without prior permission of the Ministry of Housing and Urban Affairs." The free service returns cited excerpts and points to the official source. Charging for access to manual content needs MoHUA permission first.

## Pipeline

1. `extract.py`: open the PDF with reader annotations removed; read body lines with font and position; drop running headers and footers; read the printed page label ("3 - 105").
2. `structure.py`: split into units (chapter, numbered section, table, figure caption, appendix) with stable ids such as `SEW-2013-A:3.6` and `SEW-2013-A:T3.2`. Captions accept "Table 3.7" and "Table 3-7".
3. `tables.py`: 142 of 149 sewerage tables are images. Gridlines are detected and erased, the image is OCR'd once with Tesseract, and words are assigned to grid cells. Cells that break their column's number format (a lost decimal point) are flagged, never rewritten.
4. `index.py`: SQLite with an FTS5 passage table (porter stemming; title and handle weighted above body). Long sections are split into overlapping passages; `get_clause` still returns the whole unit.
5. `service.py`: `search`, `get_clause`, `get_toc`, `list_manuals`. Exact references in a query ("Table 3.13", "para 3.25") resolve first. Every result carries a citation string and the Omakase attribution; OCR'd tables carry `needs_review` and notes.
6. `server.py`: one process, MCP over streamable HTTP at `/mcp`, REST at `/v1/search`, `/v1/clause/{id}`, `/v1/manuals`, `/v1/toc/{manual}`, `/health`.

## Quality

- `eval/questions.yaml`: questions from real APD project decisions, with expected unit ids. `omakase-cpheeo eval` scores top-k retrieval.
- `data/build/review.json`: every unit that needs a human or second-pass check, mostly OCR'd tables.

## Open items

- Table verification pass: a vision model or a person checks flagged tables against the page image; corrections are stored as overrides that survive re-ingestion.
- Official source links per manual (cpheeo.gov.in / mohua.gov.in URLs) to verify and add.
- Brand URL for attribution (`OMAKASE_CPHEEO_BRAND_URL`).
- Semantic search, if keyword retrieval misses questions phrased far from the manual's wording.
- Deployment: one small machine; public MCP URL; API keys and rate limits.
