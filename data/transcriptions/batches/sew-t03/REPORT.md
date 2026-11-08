# SEW-2013-A physical pages 323-366 (batch sew-t03): first visual reading

36 pending drafts: 32 equations and 4 tables. No record is verified and no second inspection was performed.

Source: `/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf`. SHA-256: `d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`.

All 30 assigned pages were rendered at 144 dpi with the production annotation-cleaned renderer and opened with the image tool. Every table cell and formula was then re-read from enlarged crops (288-720 dpi), and all 36 hashed source regions were finally checked together on a contact sheet built from `region_png`-equivalent clips. No OCR, no paid service, no delegation. Native PDF text was used only to locate blocks; no value was taken from it. Table 5.7 in particular is a scanned image with no extractable text.

## Page-by-page summary

Pages with targets: 335 (E5.1, E5.2), 336 (E5.3), 342 (Tp342-1), 343 (E5.4, Ep343-1), 344 (Ep344-1, Ep344-2, E5.5-E5.8), 345 (E5.9, E5.10, T5.6), 346 (E5.11, E5.12), 348 (E5.13, E5.14), 350 (T5.7), 351 (E5.15-E5.21), 356 (Ep356-1, Ep356-2), 357 (T5.8), 359 (Ep359-1, Ep359-2), 366 (E5.22-E5.25).

Pages with no target, and why:

- 323, 325, 329, 330, 334, 337, 338, 339, 341, 347, 349, 352, 358, 361, 363: prose, photographs or drawings only. Drawing part keys (Figure 5.22 items 1-6, Figure 5.17 layout numbers) and embedded drawing dimensions (Figure 5.23) are figure annotations, not data tables, and were not authored as tables.
- 347 also prints the proportional-weir worked illustration (5 cum/s to 5 m2, 3 cum/s to 3 m2) inline in prose; it was noted, not authored as an equation.
- 358 prints the clarifier sizing procedure as numbered steps 1-7 and 1-9; these are a prose procedure, not a table.
- 363 states all performance values inline in prose.

Details per page, including observations, continuations and unclear items, are in `page-report.json`.

## Draft inventory

Equations, numbered (25): E5.1, E5.2 (p335); E5.3 (p336); E5.4 (p343); E5.5, E5.6, E5.7, E5.8 (p344); E5.9, E5.10 (p345); E5.11, E5.12 (p346); E5.13, E5.14 (p348); E5.15-E5.21 (p351); E5.22-E5.25 (p366).

Equations, unnumbered or prose-inline, service locators (7): Ep343-1 (alt form after "or"), Ep344-1 (R = Vs d/nu), Ep344-2 (nu = 1.01 x 10^-6 m2/s), Ep356-1, Ep356-2 (weir length and weir loading computations), Ep359-1, Ep359-2 (worked sludge-withdrawal calculations).

Tables (4): T5.6 (p345), T5.7 (p350), T5.8 (p357), and Tp342-1 (p342), an uncaptioned, unruled two-column design-criteria list with no printed number. Tp342-1 carries `create_unit: true` with parent `SEW-2013-A:5.6.2.5`; T5.6, T5.7 and T5.8 already exist as units, so no unit creation is requested for them.

## Printed errors and oddities retained, not corrected

- (5.1) coefficient printed as 0.0729.
- (5.2) prints Sin theta with a capital S.
- (5.13) radicand printed as 2ag rather than 2g.
- (5.11) exponent printed as 1/n with no minus sign; the printed consequences (66.67 %, 58.8 %, 50 %, 33.3 % for 75 % removal) are recorded alongside as printed.
- (5.4) symbol list prints the same glyph rho for both grit and liquid density, while the formula subscripts the grit density with s.
- Table 5.6 header prints "Settling velocity m/s," with a trailing comma and the unit "m³ / d /m²".
- Table 5.7 first-column flow ranges print inconsistent hyphen spacing (30 - 45, 250 -350, 350- 500, 500- 700); all ten rows retained verbatim.
- Table 5.8 primary-clarifier "Not applicable" is a single cell spanning the Solid loading Average and Peak columns; recorded in cell_spans.
- Weir length printed as 70/93 = 75 % (75.27 % exact).
- pi printed as 3.14 in the weir-loading computations.

## Unresolved readings

None of the 36 targets contains an unreadable glyph. The only judgement calls recorded rather than resolved by the source are the interpretation of the (5.4) alternative form as a separate unnumbered target (Ep343-1), and the classification of the p342 criteria list and the p356/p359 prose computations as table/equation targets; all three are flagged in the affected drafts and in `page-report.json`.

## Checks performed

- 36/36 drafts load with the production schema rules: schema_version 1, manual-prefixed ids and unit ids, `state: pending`, no `verification.visual_recheck`.
- 36/36 source regions re-render to the recorded `render_sha256` through `omakase_cpheeo.transcriptions.region_png`.
- Table string grids agree with their Markdown for all four tables; `cell_spans` indices are zero-based and exclude the header row.
- No draft id collides with an existing record; no assigned page already holds a record.
- Every parent id was confirmed to exist as a unit by running the repository's structure parser against the source PDF: 5.6.1.9, 5.6.2.5, 5.6.2.7.1.1, 5.6.2.7.1.2, 5.6.2.7.1.4, 5.6.2.7.3, 5.6.2.8.1, 5.7.4.2.3, 5.7.4.2.5, 5.7.4.2.6.1, 5.7.4.2.6.2, 5.8.1.3.

These checks establish structure and reproducibility, not visual fidelity. A distinct second visual inspection of every record remains outstanding.

## Files written

- `data/transcriptions/batches/sew-t03/drafts/` - 36 draft records.
- `data/transcriptions/batches/sew-t03/page-report.json` - 30 page entries.
- `data/transcriptions/batches/sew-t03/REPORT.md` - this report.
- `tmp/pdfs/sew-t03/` - 30 full-page PNGs, 36 region crops, 5 contact sheets, `regions.json`, `native-text.txt`, `mkregions.py`, `sheet.py`, `author_batch.py`, `validate.py`, `report_batch.py`.

Nothing outside this batch folder and its scratch folder was written. No central record, page review, coverage file, built database, server, tunnel or Git state was touched, and the source PDF was read only.
