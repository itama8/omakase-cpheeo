# omakase-cpheeo plan

## Goal

A free, Omakase-branded service that lets engineers and their agents (Claude, ChatGPT, scripts) search the CPHEEO manuals and cite them exactly: manual, edition, part, clause or table, printed page. It is the top of the funnel for Omakase's paid civil and environmental offerings.

## Corpus

Latest parseable edition per domain. Source PDFs stay outside the repo (`OMAKASE_CPHEEO_SOURCES`, default `~/Downloads/CPHEEO`).

| Id | Manual | Status |
|---|---|---|
| `SEW-2013-A` | Sewerage and Sewage Treatment Systems, Part A: Engineering, 2013 (third edition), including all 51 listed appendices/sheets | Indexed |
| `SEW-2013-B/C` | Sewerage and Sewage Treatment Systems, Operation & Maintenance / Management, 2013 | Deferred; source PDFs unavailable locally |
| `WS-2024-A/B/C` | Water Supply and Treatment Systems, Parts A, B, C, March 2024 (fourth edition) | Indexed |
| `SWD-2019-A`, `SWD-2019-BC` | Storm Water Drainage, Vol I Part A and Vol II Parts B/C, August 2019 | Next |
| `MSW-2016` | Municipal Solid Waste Management, Parts 1-3, 2016 | Planned |

Excluded: superseded editions (1999 water supply, the May 2012 sewerage draft), commercial textbooks in the source folder (Metcalf & Eddy, the calculation manual), advisories and SOPs (phase 2).

## Licensing

The manuals are Government of India copyright: "No portion, part or whole, of this document may be reproduced/printed for any type of commercial purposes without prior permission of the Ministry of Housing and Urban Affairs." The free service returns cited excerpts and points to the official source. Charging for access to manual content needs MoHUA permission first.

## Pipeline

1. `extract.py`: open the PDF with reader annotations removed; read body lines with font and position; drop running headers and footers; read the printed page label ("3 - 105", or a plain "36"). Each manual has a `Layout` in `corpus.py`: the InDesign sewerage manual has fixed header/footer bands; the Word-generated water manual has a page number as its lowest line and mixed page sizes.
2. `structure.py`: split into units (chapter, numbered section, table, figure caption, appendix) with stable ids such as `SEW-2013-A:3.6` and `SEW-2013-A:T3.2`. Captions accept "Table 3.7" and "Table 3-7", plus lettered appendix references ("Table A7.3-1"). Native appendix contents supply the complete titles and start pages, including scanned headings and separately numbered A/B sheets. Legacy grouped handles remain available. Full-page appendix images retain formula sheets and rotated tables; printed labels are also read from sideways footers.
3. `texttables.py` (Word manuals): PyMuPDF finds the ruled grid under a caption and each cell is read by clipping the page; tables that run to the page bottom continue into an uncaptioned table at the top of the next page. Annexure tables ("Table 4") get ids like `WS-2024-A:AN6.3-T4`.
   Scanned tables use source-page crops; when a reliable crop cannot be found, the printed page is returned. Figures use full-page pictures to retain legends, vector drawings and multipart layouts. Other embedded images attach to their containing clause. No OCR is run or exposed; native PDF table text remains available. A versioned visual-transcription layer adds separately rechecked cells and math alongside the original imagery; see `docs/visual-transcriptions.md` for incomplete coverage.
4. `transcriptions.py`: source-pinned, versioned visual records under `data/transcriptions/records/` are reapplied during ingestion or offline snapshot refresh. Verified records add searchable numerical/math passages; equation handles retain source crops. Pending/unclear records retain evidence without verified numerical text. Source/render/content digests reject drift.
5. `index.py`: SQLite with an FTS5 passage table (porter stemming; title and handle weighted above body). Long sections are split into overlapping passages; `get_clause` still returns the whole unit.
6. `service.py`: `search`, `get_clause`, `get_toc`, `list_manuals`. Exact references in a query ("Table 3.13", "para 3.25", "Annexure 6.1") resolve first. Synonym concepts match query words even with intervening qualifiers ("minimum gravity sewer diameter" also searches for "minimum size"). Expansions are matched as phrases, and when a query names only one domain's terms (sewer, manhole / WTP, service reservoir) that domain's results rank higher; nothing is filtered. Every result carries a citation string and the Omakase attribution; image references carry printed and physical page numbers.
7. `server.py`: one process, MCP over streamable HTTP at `/mcp`, REST at `/v1/search`, `/v1/clause/{id}`, `/v1/manuals`, `/v1/toc/{manual}`, `/health`.

## Quality

- `eval/questions.yaml`: questions from real APD project decisions, with expected unit ids. Before visual transcription the unchanged set scored 26/27 top five (MRR 0.76); with the current verified records it scores 27/27 (MRR 0.84), and L20 now finds the transcribed design-period table at rank one. Handle retrieval alone is not answer correctness: Table 3.15 contains a printed caption/content mismatch. These source-open questions are optimistic regression checks.
- `eval/verified-transcriptions.yaml` and `scripts/check_verified_retrieval.py`: 45/45 top-five numerical/formula content checks, 40/45 rank one, MRR 0.937. Check actual retrieved rows, coefficients, source discrepancies, continuation pages and evidence links. Report local latency separately from network/model time. `scripts/test_transcriptions.py` verifies re-ingestion, idempotence, removal/demotion, changed evidence rejection and unclear-image fallback. See `docs/visual-transcriptions.md` for the unfinished scope.
- `eval/search-ranking.yaml`: ChatGPT-feedback paraphrases plus slope, velocity, water and explicit-reference controls. Run `omakase-cpheeo eval --questions eval/search-ranking.yaml -k 1 -v`. The direct diameter clause now ranks first in all eight diameter/size variants; the 12-query set improves from 6/12 to 12/12 first results. The exact ChatGPT tool query was not supplied, so these are targeted regression checks rather than an independent accuracy estimate.
- `eval/sewage-appendices.yaml`: 13/13 appendix queries in the top five, MRR 0.92. `scripts/check_appendix_coverage.py` verifies all 51 source-listed appendix/sheet titles, their page boundaries, and full-page images covering all 185 printed appendix pages. This does not verify a model's interpretation of the numerical images.
- `scripts/test_image_delivery.py` checks source-image storage, page references, complete multipage delivery and picture ownership. `scripts/mcp_smoke.py` checks direct diameter criteria rank first and other expected search results are within the requested three results, native table text, MCP image blocks, HTTP image bytes and citation pages.
- `data/build/review.json`: every unit that needs a human or second-pass check, units with extraction concerns.

## Open items

- Complete the ongoing all-page visual inventory and transcription: see `data/transcriptions/coverage.json` and `docs/visual-transcriptions.md`. The current 276 verified records do not fulfill the full scope; assistants must disclose unclear values rather than guess.
- Official source links per manual (cpheeo.gov.in / mohua.gov.in URLs) to verify and add.
- Brand URL for attribution (`OMAKASE_CPHEEO_BRAND_URL`).
- Semantic search, if keyword retrieval misses questions phrased far from the manual's wording.
- Deployment: one small machine; public MCP URL; API keys and rate limits.
