# sew-t02 first-pass visual transcription (draft only)

Manual: SEW-2013-A, source `"/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf"`
(sha256 `d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`).
Assigned physical pages: 30 (247, 254, 255, 257, 260, 261, 262, 266, 267, 271, 277, 279, 280, 285, 288,
290, 291, 292, 298, 299, 302, 303, 315, 316, 317, 318, 319, 320, 321, 322).

## Method

- Every assigned page was rendered at 144 dpi from the annotation-cleaned document
  (`open_clean`) into `tmp/pdfs/sew-t02/page-<n>.png` and viewed directly. No OCR, no paid API,
  no delegation.
- Pages 260, 298 and 303 are printed landscape inside a portrait page. Those page images were also
  rotated and re-viewed, and each item there was read from 200 to 600 dpi crops of the same render.
- Every draft bbox was checked by rendering it through `region_png`, rotating where needed, and
  viewing the result; the stored `render_sha256` is the sha256 of that exact render and was
  re-verified against the record after writing.
- Nothing already present in `data/transcriptions/records/` was drafted (checked by id: no existing
  record covers any of these 30 pages; E3.46 and E3.47 are both absent from the baseline, and T5.5
  is absent).

## Draft counts

| kind | count | ids |
| --- | --- | --- |
| table | 6 | T5.5, Tp291-1, Tp298-1, Tp302-1, Tp303-1, Tp303-2 |
| equation | 5 | E3.47, Ep260-1, Ep260-2, Ep288-1, Ep290-1 |
| **total** | **11** | |

All drafts are `state: "pending"` with only `verification.transcription` present; no
`verification.visual_recheck` and no second visual pass was performed.

Numbered items: 2 (equation 3.47 and Table 5.5). Unnumbered items: 9, using `p<page>-<k>` service
locators only, never printed numbers.

## Pages with no target

19 of the 30 pages carry no table and no equation. They hold figures: line drawings, labelled
schematics, photographs and charts (3.53 to 3.61, 4.1 to 4.5, 4.11, 4.13 to 4.16 charts, 5.6 to
5.15). Figure callout labels, chart annotations and lettered lists were not transcribed as tables
or equations. Each such page has a `no_targets_reason` in `page-report.json`.

Four pages only point at an item printed elsewhere: p247 to Table 3-27 (p248), p271 to Table 3.30
(p272), p288 to Table 4-2 (p289), p318 to Table 5.5 (p319, in this batch). These are recorded as
`continuations`.

## Printed errors and oddities (kept verbatim, flagged in `notes`)

- p262 (E3.47): the formula is an increment `ΔC_s` while the printed symbol list names `C_s`; `BOD_T`
  is used but not defined on the page.
- p260 (Ep260-2): the two sides of the sulphide oxidation are joined by a horizontal dash, not by a
  reaction arrow as printed for the pipe-wall reaction in the same figure.
- p288 (Ep288-1): the inline expression `V²/2g` is unnumbered and neither `V` nor `g` is defined.
- p291 (Tp291-1): header printed `No. OF PUMPS IN OPERN`; the chart labels print `H = f (o)` where
  `(Q)` is presumably intended.
- p298 (Tp298-1): the equipment schedule gives bare `RS / D / W / V` designations with no expansion,
  and its last two grid rows are merged full-width notes (year 2041 for civil work, year 2026 for the
  pump).
- p302 (Tp302-1): the printed unit in the spanning heading is a bare vertical stroke; transcribed as
  `lps`, the abbreviation used in the pumpage boxes of the same figure.
- p303 (Tp303-1): `11.5-13=(-)1.5` prints the negative result in parentheses.
- p303 (Tp303-2): `11.5+1.5+2=15m` prints the unit inside the cell; the chart label reads
  `Hydraulic grade line oroginal`.
- p319 (T5.5): row (ii) `Stabilisation` and row (iii) `Stabilization` differ in spelling; the last
  header cell is printed on two lines as `Total` / `Coliform`.

## Unclear items

No item was transcribed as "unclear"; every glyph in the 11 drafted items was legible at the zoom
levels used. Residual uncertainty is record-level and is stated in the draft `notes`:

- p260: the two relations sit inside a small scanned figure, so stroke weight is coarse, but both
  sides of each relation read cleanly.
- p302: only the capitalisation of the unit's first letter is undecidable (`Ips` versus `lps`).
- p303: the arithmetic in both condition tables is internally inconsistent with the printed levels
  (for example the B-column ground level changes from 12 to 13 between the two tables). The values
  are transcribed as printed; nothing was reconciled or recomputed.

## Files

- `drafts/*.json`: 11 pending draft records.
- `page-report.json`: one entry per assigned page, all 30 present.
- `tmp/pdfs/sew-t02/`: the 30 full-page renders plus the detail crops used for reading and bbox checks.
