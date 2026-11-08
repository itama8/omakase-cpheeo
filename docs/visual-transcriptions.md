# Visual transcriptions and coverage

The user narrowed the workflow on 2026-11-08: **small batches of selected tables/equations, without inspecting every page**. All 18 active page-range/recovery tasks were stopped and their saved files preserved. `data/transcriptions/work-policy.json` records the current policy: normally five targets, one active batch, at most one delegated worker, no automatic expansion across manuals.

Select concrete targets from the existing inventory, saved drafts, extraction-failure signals or retrieval needs. Inspect their source crops and only the continuation/context needed to transcribe them. Complete, separately recheck and validate that selected batch before choosing another. Whole-page discovery is not a prerequisite. Explicit mathematical expressions inside figures remain eligible targets; relationships stated only in prose are not converted into invented notation.

`data/transcriptions/coverage.json` is the reproducible coverage ledger. It retains historical page counts as audit metadata, not an outstanding work queue. A verified crop establishes only its record; its page is marked partial unless an actual whole-page review was performed. Exhaustive manual coverage and a total equation count are not claimed.

## Current checkpoint

All four PDF hashes and all 3,213 physical pages are inventoried. The earlier whole-page review ledger records 341 completed pages. Eleven pages have partial reviews, including the selected crop reviews from `targeted-sew-01` and `targeted-sew-02`. These counts describe past review coverage, not a requirement to inspect the other pages.

There are 295 verified records (136 tables, 159 equations) and one unclear record:

- Sewage Part A: 115 tables and 149 equations. Completed batches include the previously documented Chapter 1-4 work and selected Chapter 5 treatment, disinfection, electrical and piping material, Chapter 6 and appendix pages. Batch page reports enumerate the reviewed pages; gaps between them are unreviewed.
- Water Part A/B/C: 21 tables and ten equations, including Part A Tables 1.1-1.3 (physical pages 91-92, 95-96), Part B Tables 1.1 and 1.2 (physical pages 72, 74-76), and Part B Tables 3.2 and 3.3 (physical pages 110-111, 115-116) and all nine tables marked image-only in the baseline index and selected headloss mathematics. Other native tables and water formulas are not visually verified unless explicitly covered by a record and may be selected for a later batch.
- The `water-a-t02` parent comparison added Table 2.1 and three unnumbered expression groups from Figure 1.7. The first reading had excluded its explicit NRW equalities and inequalities as figure labels; parent discovery corrected that scope error, authored the expressions, and performed a distinct second comparison. No equations were invented for relationships stated only in prose.
- Of 201 baseline image-only tables, 112 have verified transcriptions and 89 do not yet have one. These are baseline unit counts, not a claim that visual discovery is finished.
- An earlier parent recheck added 14 records from `sew-t05`: Tables 5.17-5.27, Equation 5.43, the critical-parameter panel of Table 5.18 and a repeated chart location key. The second comparison corrected Raibarreilly and Dakshineswar spellings and removed an inferred vertical cell merge. Printed numerical outliers, missing row 3 in Table 5.26 and undefined N in Equation 5.43 remain documented as printed.
- `SEW-2013-A:Ep180-1` remains unclear: the printed water-cushion expression is `h1/2 d1/3` on the baseline, without clear power notation even in a 288-dpi close-up. It returns a source-region image and an explicit ambiguity note, without asserted LaTeX or verified math.

The committed coverage JSON was stale after earlier batches because `visual_coverage.py` prints its result; it has now been refreshed from the records and review ledger. Regenerate the saved file explicitly when recording the next checkpoint.
`page-reviews.json` records completed/partial pages and remaining concerns. The source-pinned `*-pages.json` ledgers include every physical page, embedded-image/vector signals, existing table handles and original source-image references. `table-inventory.json` inventories all 535 baseline table units. None of these automated signals is counted as visual verification.

## How records work

Authored JSON records live under `data/transcriptions/records/`, outside gitignored derived indexes. Each records the manual/unit, full PDF SHA-256, physical and printed page, crop in PDF points, and SHA-256 of the exact annotation-cleaned source-region PNG rendered at 144 dpi. Source PDFs and temporary renders are not committed.

Tables retain string-valued cells (including trailing zeros, comma grouping, printed mistakes and blanks), searchable Markdown, expanded or explicit merged-cell relationships, and source notes. Formulas retain LaTeX, readable math, printed definitions/units and applicability. Parent sections expose their equations; equation handles use `E`, for example `SEW-2013-A:E5.30`. Unnumbered locators use physical pages, such as `Ep272-1`; these are explicitly identified as service locators rather than printed equation numbers.

Every verified record has a first visual reading and a distinct second visual comparison, with observations and a digest binding the recheck to the authored content. Both passes were performed by the same assistant; this is **not independent human review or a claim of perfect accuracy**. Changed authored content invalidates verification. Changed source PDF or rendered crop rejects the complete application batch. No OCR or paid external vision/API is used.

Verification concerns transcription fidelity. It does not certify the manual's engineering correctness. Printed discrepancies are preserved with separate notes, including:

- Table 3.15's manhole caption above sulphide-generation cells; no diameter values are invented.
- Table 3.12's malformed decimal strings.
- The asymmetric pair in Table 3.21 and the reinforcement discrepancy between Tables 3.22 and 3.24.
- Table 3.31's two different maximum-spacing rows.
- Equation 3.5's full-angle tangent wording and the following inconsistent tangent assertion.
- Equation 3.41's visible `NZq` denominator, Equation 3.43's printed interaction expression, and undefined symbols/log bases where the source does not define them.

The second pass corrected actual first-pass transcription errors before verification: Table 3.6's rectangle/pervious/10-minute coefficient is `0.149`, and Annexure 6.3 Table 6's Pipe 8 speed is `2.974`. These corrections and the source comparisons are recorded in the verification observations.

## Applying and checking

Full `ingest` automatically validates and applies the versioned records. To add records to an existing **offline copy** of the unchanged baseline index:

```sh
uv run omakase-cpheeo --db /path/to/offline/cpheeo.sqlite apply-transcriptions
uv run python scripts/visual_coverage.py
uv run python -m unittest discover -s scripts -p 'test_*.py'
uv run python scripts/check_verified_retrieval.py /path/to/offline/cpheeo.sqlite
uv run python scripts/mcp_smoke.py http://127.0.0.1:8799/mcp
```

Refresh writes a replacement snapshot, preserves original native content and image URLs, and adds source-region crops. Reapplying is idempotent. Removing or demoting a record removes its verified passages; pending/unclear content never enters the numerical/formula search text. Unclear equations keep a searchable title and image fallback. REST, MCP and HTML expose the same verified text and provenance. Existing native table fields remain native extraction; visual cells are explicitly under `verified_transcriptions[].rows`.

Do not regenerate the page inventory as a substitute for actual review. Regeneration preserves the separate page-review ledger, but its detections still require inspection. Do not mark a page complete until all its transcription targets and continuations are accounted for.

## Validation limits

`eval/verified-transcriptions.yaml` checks retrieved values/formulas, full numerical rows, anomalies and continuations. At this checkpoint, 64/64 queries retrieve the expected content in the top five, 53/64 at rank one, MRR 0.909. The original APD set and ranking/appendix regressions must also pass. The manhole query's expected handle alone is not proof that its source contains manhole sizes.

The checks were authored with sources open and are optimistic regression checks, not independent retrieval accuracy measurements. The checker reports measured local warm SQLite search-plus-fetch latency, excluding network, image rendering and model time. `data/transcriptions/validation.txt` records the measured run. Source digests prevent drift; automated checks cannot establish that a human/assistant read every glyph correctly.

## Remaining work

Choose the next small set of named table/equation targets when continuing. Reuse saved candidates where useful; preserve unresolved or ambiguous regions explicitly. Do not restart the stopped broad page sweeps or automatically fan out across manuals. The latest targeted batch verified the five sludge-treatment Tables 6.6-6.10. The earlier targeted batch covered Tables 5.52, 5.53, 5.55, 5.56 and 5.57; other candidates remain available for later selection. Normative-vs-example reranking remains open; no query-specific expected-id boost has been added.

The public base remains `https://arlington-accepting-lip-insertion.trycloudflare.com`. Only deploy a fresh tested application snapshot; preserve the existing Cloudflare tunnel and old application snapshot for rollback. Never regenerate the tunnel to deploy transcription records.
