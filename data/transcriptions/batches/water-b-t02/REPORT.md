# WS-2024-B physical pages 95, 96, 97, 110, 111, 112, 114, 115, 116, 120 — first-pass visual transcription

Source: `/home/a2ajinkya/Downloads/CPHEEO/Water Supply_2023/Part-B-Manual-Operation-and-Maintenance(5).pdf`,
SHA-256 `1cfd336b3e2928b95cec3899d3e1d15807b5598d78730d6fe3eef381021844e7`, which matches the `WS-2024-B`
entry in `data/transcriptions/sources.json`. Opened read-only; annotation removal happened in memory through
`open_clean` only. No OCR, no native-text authoring (native text was used only to locate block and grid
coordinates, never as the source of a value), no delegation, no commit, no server or tunnel, and no writes
outside `data/transcriptions/batches/water-b-t02/` and `tmp/pdfs/water-b-t02/`.

Every one of the ten assigned pages was rendered at 144 dpi, saved to `tmp/pdfs/water-b-t02/page-<n>.png`,
and viewed with the image tool in this run. Small glyphs, split cells and grid geometry were re-read from
clipped 288–600 dpi region zooms (`zoom-110-table.png`, `zoom-111-table.png`, `zoom-115-table.png`,
`zoom-116-table1.png`, `zoom-116-table2.png`, `zoom-116-ranney.png`).

## Counts

| Item | Value |
| --- | --- |
| Pages assigned | 10 |
| Pages inspected | 10 |
| Pages with a target | 4 (110, 111, 115, 116) |
| Pages with no target | 6 (95, 96, 97, 112, 114, 120) |
| Distinct table ids drafted | 2 (`WS-2024-B:T3.2`, `WS-2024-B:T3.3`) |
| Equation ids drafted | 0 |
| Unnumbered targets (`T p<page>-<k>`) | 0 |
| New drafts written | 2 |
| Duplicate ids skipped | 0 |
| Continuation pages rendered beyond the assignment | 0 (both continuations were inside the assignment: 110→111 and 115→116) |
| Unclear / unreadable items | 0 |

## Drafts

| Id | Kind | Title as printed | Pages (printed labels) | Candidate path |
| --- | --- | --- | --- | --- |
| `WS-2024-B:T3.2` | table | Lake and Pond Restoration Methods | 110 (43), 111 (44) | `drafts/WS-2024-B--T3.2.json` |
| `WS-2024-B:T3.3` | table | Operation and Maintenance of Intake for the Abstraction of Groundwater | 115 (48), 116 (49) | `drafts/WS-2024-B--T3.3.json` |

Both drafts are `"state": "pending"` with `source_sha256` and a `regions[]` entry per printed page carrying the
PDF-point bbox and the `render_sha256` of `omakase_cpheeo.transcriptions.region_png(doc, region)` for that
region. No `verification.visual_recheck` block is present and no content digest is claimed; sealing and the
independent second visual comparison belong to the parent.

### Unit and parent handling

`WS-2024-B:T3.2` and `WS-2024-B:T3.3` both already exist in the baseline index
(`data/build/cpheeo.sqlite`, `units`, `kind = 'table'`, read-only query). Per the brief neither draft sets
`create_unit` and neither sets `parent_id`. Enclosing units for reference, from the same read-only query, are
`WS-2024-B:3.4.7` (Ponds and Lakes) for T3.2 and `WS-2024-B:3.5.3` (Intake for Abstraction of Groundwater)
for T3.3.

No equation was found on any assigned page, so no equation draft exists in this batch and the "every equation
needs `parent_id`" rule has no instance to apply here.

### Pending sibling candidates

A repo-wide check of `data/transcriptions/records/` and every `batches/*/drafts` and `batches/*/records`
directory found no pending candidate for `WS-2024-B:T3.2` or `WS-2024-B:T3.3`, and no other pending draft
whose regions fall on pages 95–120 of this manual. There is therefore no pending sibling to cite for these
ids and no id was silently absorbed: the two drafts above are the only candidates and are new. `WS-2024-B:T3.1`
and `WS-2024-B:T1.1`/`T1.2` are already verified in `data/transcriptions/records/` and lie on other pages
(105–109 and 72–76), so they were not touched.

## Every-page observations

- Physical 95 / printed 28 — `page-95.png`. Figure 2.4 *Computerised Revenue Management System*: labelled flow
  schematic (SAJALA boxes, screen thumbnails, an in-artwork orange strip reading `SAJALA - Revenue Billing
  Collection and Management System for BWSSB`, `(Source: BWSSB)`) and surrounding 2.6.10 prose. Diagram, not a
  table; no equation. Printed oddities inside the artwork: `91 Automated` hanging on its own line above
  `...Kiosks`.
- Physical 96 / printed 29 — `page-96.png`. Figure 2.5 *Valve Monitoring System* (IVRS bullet column, BWSSB
  Engineers → Ground Level Staff → Valve Monitoring Service (VMS) → CMS Call Centre, Households), then
  2.6.11 Planning for Exigencies, 2.7 Capacity Building and the start of 2.7.1 Job Database. No target.
  The in-artwork caption `Major elements of online water quality monitoring` does not match the numbered
  figure caption; both left as printed.
- Physical 97 / printed 30 — `page-97.png`. End of 2.7.1, 2.7.2 Training Requirements with a five-item bullet
  list, 2.8 Ensuring Efficient O&M, and 2.8.1 Specific Key Performance Indicators (KPIs) items a)–d). Prose and
  lists only; `IS 10500 (2012)`, `Table 2.7`, `at least 15%` are prose references, not formulas.
- Physical 110 / printed 43 — `page-110.png`, zoom `zoom-110-table.png`. End of 3.4.5 Sea Water prose, 3.4.6,
  3.4.7 Ponds and Lakes, then Table 3.2 starts at the page foot: caption, three-column header
  (`S. No. / Restoration Methods / Anticipated Achievements`) and rows 1–3. Drafted; continues on 111.
- Physical 111 / printed 44 — `page-111.png`, zoom `zoom-111-table.png`. Table 3.2 continuation: header row
  restated, rows 4–6, table foot at mid page. Below it a boxed sidebar `Restoration of Dal Lake:` (prose plus two
  photographs, `Source: J&K (LCMA)`, `60,000 m2` with a superscript 2) — a sidebar, not a table — then 3.4.8
  Pond and Lake Maintenance Equipment with lettered items A. Dredgers to D. Aquatic Skimmers.
- Physical 112 / printed 45 — `page-112.png`. Items E. Lake Rakes and F. De-Icers, a closing paragraph, a boxed
  sidebar `Robotic inspection, cleaning, and repair of underwater assets:` with two captioned photographs
  (`Robotic Inspection`, `Robotic Dam Desilting`), then 3.5 Groundwater and the opening bullet list. No target.
- Physical 114 / printed 47 — `page-114.png`. Figure 3.8 *Yield draw-down curve* (line chart, axes `PERCENT YIELD`
  and `PERCENT DRAW DOWN`, ticks 0–100 only, two thin construction lines), end of 3.5.1 Preventive Maintenance,
  3.5.2 Determining Static Water Level (SWL) methods (a) Electric sounder, (b) Wetted tape, (c) Airline. The chart
  prints axis ticks but no plotted numbers, so no values were inferred and no tabular or equation target was
  raised.
- Physical 115 / printed 48 — `page-115.png`, zoom `zoom-115-table.png`. Figure 3.9 *Airline installed in a
  tubewell for measuring water level* (labelled section drawing with `A - D`, `B`, `C`, `E`), item (d) Tubewell
  sounding, 3.5.3 and Table 3.3 opening: caption, header (`Intake / Monthly/Quarterly / Yearly`), the complete
  Dug well row and the first part of the Hand pump (HP) row. Drafted; continues on 116.
- Physical 116 / printed 49 — `page-116.png`, zooms `zoom-116-table1.png`, `zoom-116-table2.png`,
  `zoom-116-ranney.png`. Table 3.3 continuation: header restated, the split Hand pump row finishing in a row
  whose Intake cell is printed blank, then Tube/Borewell, Infiltration gallery and Radial collector wells
  (Ranney Wells); then 3.5.4 Groundwater Collection System, 3.5.5 Storage Components and the first storage
  bullet that runs on to page 117.
- Physical 120 / printed 53 — `page-120.png`. Impression-block procedure in prose (2.0 cm, about 1.0 cm,
  about 5.0 to 7.0 cm), Figure 3.10 *Impression Block* (labelled tool section drawing) and item
  b) Fishing Tools to Recover Fallen Objects. Prose measurements only; no equation, no table.

## Printed errors preserved (observations only, nothing corrected)

- Page 95: artwork label `91 Automated` set on its own line, and `...Kiosks` printed with a leading ellipsis.
- Page 96: `bioterrorism` set flush inside the emergency list (`water supply bioterrorism`); in-artwork caption
  does not match the numbered caption.
- Page 97: `promotions incentives`; `don'ts` with a straight apostrophe.
- Table 3.2, row 1: `biomanipulation with remove of cyprinids`; `phosphorous inactivation`.
- Table 3.2, row 2: `NO3/PO4/BOD` printed without subscripts.
- Table 3.2, row 4: `Reduction is phosphorous organic matter` (`is` where the parallel rows read `in`).
- Table 3.2, row 5: `lake/s`.
- Table 3.3: the Hand pump (HP) row is split by the page break and its continuation row on page 49 prints a
  blank Intake cell; `Radial collector wells (Ranney Wells)` prints a capital `W` inside the parenthesis;
  bullet punctuation is inconsistent between rows.
- Page 112: `The dredgers and aerators used described above` (repeated `used`); `remotely- operated`.
- Page 120: the figure label reads `PARAFFIN WAX OR OTHER PLASTIC METERIAL`; prose reads
  `... is poured into the cylinder is left to cool and solidify.`

## Files written

- `data/transcriptions/batches/water-b-t02/page-report.json` — all ten assigned pages, each with page label,
  targets, `no_targets_reason`, continuations, `unclear`, the viewed PNG path and its SHA-256.
- `data/transcriptions/batches/water-b-t02/drafts/WS-2024-B--T3.2.json`
- `data/transcriptions/batches/water-b-t02/drafts/WS-2024-B--T3.3.json`
- `data/transcriptions/batches/water-b-t02/REPORT.md` (this file)
- `tmp/pdfs/water-b-t02/` — ten 144 dpi page renders, six region zooms, and the throwaway report helper
  `report_append.py`.

Nothing was written to `data/transcriptions/records/`, `page-reviews.json`, `coverage.json`, `data/build/`,
or any other batch directory, and no verification pass id was claimed beyond the first-pass transcription note.

## Status

All ten assigned pages were visually inspected and the two tables that appear on them are drafted as pending
candidates. Parent work remaining: visual comparison of both drafts against the printed pages, the independent
second inspection and content digest, and sealing/promotion of `WS-2024-B:T3.2` and `WS-2024-B:T3.3`.
