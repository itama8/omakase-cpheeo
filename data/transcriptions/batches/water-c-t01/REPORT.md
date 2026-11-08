# Batch water-c-t01 — WS-2024-C draft visual transcription

Manual: WS-2024-C (Part C — Management), 265 physical pages.
Assigned physical pages: 66, 67, 69, 70, 71, 74, 78, 79, 80, 81 (printed 14, 15, 17, 18, 19, 22, 26, 27, 28, 29).
Method: pages rendered from the annotation-cleaned source at 144 dpi with `open_clean`, every page viewed, small
glyphs and merged cells re-read from 260–300 dpi `clip` crops. No OCR, no paid API. Rulings were also read as
vector geometry (column x / row y) and used only to confirm cell spans that were then read visually.

## Source verification

`sha256(Part-C-Manual-Management(4).pdf) = f1cc3a56b1cb4dc0d1c140a3d0f9731ff4e5e1c8273a3ebb225b47db4ae3c29c`,
identical to `data/transcriptions/sources.json` for WS-2024-C. The PDF was opened read-only.

## Targets found and drafted

| Page | Printed | Target | Result |
| --- | --- | --- | --- |
| 66 | 14 | `WS-2024-C:T2.2` Comparative Institutional Roles … among Select States | draft, rows 0–7 (caption + 2-row header + 8 cell rows) |
| 67 | 15 | `WS-2024-C:T2.2` (continuation) | draft, row 8 `Municipal Departments`, header repeated |
| 71 | 19 | `WS-2024-C:T2.3` Service Level Benchmark – Indicators Related to Water Supply | draft, 9 rows, complete on page |
| 78 | 26 | `WS-2024-C:T3.1` Recommendations of the Environmental Hygiene Committee | draft, 3 rows, one printed blank cell |
| 79 | 27 | `WS-2024-C:T3.2` Staff Functional Groups … relevant Roles for Water Service Delivery | draft, 6 rows, 3 group spans + 1 shared roles cell |
| 80 | 28 | `WS-2024-C:T3.3` Core functions and Responsibilities … Providers | draft, rows 0–1 (Technical, Commercial) |
| 81 | 29 | `WS-2024-C:T3.3` (continuation) | draft, rows 2–7 incl. printed band `Additional or Cross Cutting Functions` |

Drafts, all `state: "pending"`, with `regions` and recomputed `render_sha256`, in
`data/transcriptions/batches/water-c-t01/drafts/`:

- `WS-2024-C--T2.2.json` (2 regions: pages 66, 67)
- `WS-2024-C--T2.3.json`
- `WS-2024-C--T3.1.json`
- `WS-2024-C--T3.2.json`
- `WS-2024-C--T3.3.json` (2 regions: pages 80, 81)

Renders viewed: `tmp/pdfs/water-c-t01/page-{66,67,69,70,71,74,78,79,80,81}.png`, plus crops
`p66-*.png`, `p67-*.png`, `p71-t23.png`, `p78-t31.png`, `p79-t32.png`, `p80-t33-*.png`, `p81-band.png` in the same folder.

## Pages with no table or equation

- **69 (17)** — AMRUT reform-agenda prose and 2.3.2.2 AMRUT 2.0. Only running-text figures (`Rs. 3,840 crores`,
  `Rs. 26 crores (at Rs. 13 crores per Rs. 100 crore)`, `24×7 PWS`); nothing set as a formula or table.
- **70 (18)** — rest of the AMRUT 2.0 features, PPP/reform-agenda prose, 2.3.3 and 2.3.3.1. Percentages occur
  inside sentences only.
- **74 (22)** — landscape page holding only Figure 2.1, the Maharashtra Water Resources Regulatory Authority
  organisational chart (embedded image bbox [73.4, 104.1, 772.5, 430.2] pt). Boxes carry post titles only, no
  mathematical callouts. It is a figure, out of scope for this table/equation batch.

## Continuations and boundaries

- `T2.2` runs 66 → 67 (label 14 → 15). Both pages are inside the assignment; no out-of-assignment page was needed.
- `T3.3` runs 80 → 81 (label 28 → 29). Ends on page 81 at y = 506.1 pt, before section 3.1.4; no extra page needed.
- No assigned page contained an unnumbered table or a set equation, so no `E p<page>-k` or `T p<page>-k` id was created.

## Printed oddities preserved (not corrected)

- `Orissa (WATCO)` in `T2.2` (Odisha is the current name) — kept, noted.
- `State- level specialist agency` in the Capital works column, space after the hyphen — kept, noted.
- `Chhattisgarh` is printed with the double `h` and was confirmed at 300 dpi; it matches the standard spelling and
  is not an error.
- Fully justified cells break words across lines with wide inter-word gaps
  (`Kerala (KWA)    Jharkhand (WSSD    + JUIDCO)`); lines are joined with single spaces, wording and marks unchanged.
- `T2.2` prints some State Examples lists with commas and others one name per line without commas
  (`Karnataka`/`Maharashtra`/`Tamil Nadu`/`Punjab`/`Uttar Pradesh` and `Delhi`/`Shimla`); no separators were added.
- `T3.1` third row right-hand cell is printed blank; recorded as `""`, nothing inferred.
- `T3.2` prints `relevant Roles` with a lower-case `r` — kept.
- `T3.3` responsibility cells are printed bullet lists; bullet glyphs are not emitted as text, each item is a
  separate line in printed order (matching the repo convention for multi-item cells).
- `T3.3` prints an internal full-width bold band `Additional or Cross Cutting Functions`; recorded as a
  `colspan: 2` row rather than as a data value.
- En dashes in `T3.3` (`Asset management – conducting`, `Financial – this is…`, `Laboratory – this should be…`,
  `MIS) – this is…`) and in the `T2.3` title are kept as printed.

## Catalogue, units and record checks

- Read-only `units` queries (`data/build/cpheeo.sqlite`, mode=ro): `WS-2024-C:T2.2`, `T2.3`, `T3.1`, `T3.2`, `T3.3`
  all exist as baseline indexed units (pages 66-67, 71, 78, 79, 80-81). Therefore **no draft sets `create_unit`
  or `parent_id`**.
- No equation records were produced, so no `parent_id` was required and no section unit id was assigned.
- Baseline `units` has no equation units in chapters 2–3, consistent with the visual finding of no set equations.
- `data/transcriptions/records/` holds no record for any of these five ids (only `WS-2024-C--T2.1.json`, already
  `verified`, page 64) — no duplicate was created.
- Promoted-record title note: the baseline unit title for `T2.2` stops at `…among`. The draft stores the full
  printed title `…among Select States`; the parent may align or annotate this during sealing.

## Pending sibling drafts

No pending sibling draft exists for any WS-2024-C id in this batch. Other batch folders do contain pending drafts
for other manuals and were not used as evidence, e.g.
`data/transcriptions/batches/water-b-t02/drafts/WS-2024-B--T3.2.json` and
`data/transcriptions/batches/water-b-68-79/records/WS-2024-B--T1.1.json`.
These five drafts are unverified by design: they stay `pending` until the parent compares every target cell and
seals them. **Parent promotion required** — no record here may be treated as verified or copied into
`data/transcriptions/records/` on this batch's authority.

## Constraints honoured

Writes confined to `data/transcriptions/batches/water-c-t01/` and `tmp/pdfs/water-c-t01/`. No writes to
`records/`, `page-reviews.json`, `coverage.json`, `data/build/`, no server/tunnel changes, no commits, no
delegation. DB access was read-only.
