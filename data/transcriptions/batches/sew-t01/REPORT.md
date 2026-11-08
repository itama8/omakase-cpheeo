# sew-t01: first-pass visual transcription (SEW-2013-A, physical pages 89-246)

3 pending equation drafts (1 numbered, 2 unnumbered figure expression sets). No table drafts. No record is verified.

Source: `/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf`. SHA-256: `d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`.

All 30 assigned full-page PNGs were rendered with the production annotation-cleaned reader and were actually viewed with the image-reading tool. Small glyphs, fraction numerators and vertical callouts were re-read from 288 dpi and native-raster crops. No OCR, no paid service, no delegation, no native text used as a completeness proof.

## Counts

- Assigned pages: 30. Pages with a target: 3 (159, 230, 236). Pages with no target: 27.
- Drafts: 3. Kinds: 3 equation, 0 table.
- Numbered equations drafted: 1 (`3.46`). Unnumbered figure expression sets drafted: 2 (`p159-1`, `p230-1`).
- Continuations recorded: 5. Unclear items: 1 (see below).

## Drafts

| id | page | label | basis |
| --- | --- | --- | --- |
| `SEW-2013-A:E3.46` | 236 | 3 - 91 | Numbered equation, safety factor as field over safe supporting strength |
| `SEW-2013-A:Ep159-1` | 159 | 3 - 14 | Unnumbered expressions inside Figure 3.5: W = 5D/12, t = D/6, with D and H defined |
| `SEW-2013-A:Ep230-1` | 230 | 3 - 85 | Unnumbered dimension expressions inside Figure 3.46, bedding classes A-D |

Both unnumbered ids are service locators, not printed numbers; each draft says so in `notes`. Each region `render_sha256` was recomputed from `omakase_cpheeo.transcriptions.region_png` and matches. `load_records` accepts all three files.

`Ep230-1` follows the existing Figure 3.48 record (`SEW-2013-A:Ep233-1`), which likewise captures the printed bedding dimension expressions of a chapter 3 bedding figure as an unnumbered equation. The parent may drop that convention; the draft states the judgement in its notes.

## Pages with no target

Most of this page range is text plus figures. The image signal that selected these pages came from photographs and engineering drawings, not from hidden tables. Specifically: 89 (Figure 1.1 box chart), 98 (flowchart), 158 (Figures 3.3 and 3.4), 160, 163, 167, 170, 184, 187, 189, 190, 192, 193, 194, 195, 196, 197, 200, 205, 206, 227, 239, 245, 246. Pages 91, 111 and 146 are text only and cite tables printed elsewhere (Table 1.1 on page 92; Table 2-1 on page 112).

Two no-target calls worth the parent's attention:

- Page 158: Figures 3.3 and 3.4 carry geometry callouts only (`2Hmax minimum`, `L Crest Length`, `Hmax`, `8R`, `3R`, `R`, `2R`, `0.867R`, `1.2R`, `0.333R`, `0.5R`, `0.234R`). No relation is stated and R is never defined in print, so no equation draft was made, consistent with the earlier 304-313 batch treatment of Figure 4.17. Unlike page 159, there is no defined symbol and no printed equality.
- Page 89: Figure 1.1 prints its data in boxed rows (Household Toilet 81.4 %; No Household Toilet 18.6 %; Septic Tanks 38.2 %; Pit Latrine 8.8 %; Insanitary (Dry & Bahao) Latrines 1.7 %; Sewerage Connection 32.7 %; Community Toilets 6 %; Open Defecation 12.6 %). It is a two-level chart rather than a grid, it is captioned as a figure, and every value is repeated in the body text of the same page, so no table draft was made. The values are listed in `page-report.json` if an unnumbered `Tp89-1` record is wanted.

## Unclear

- Page 230, Figure 3.46: the callout `0.125 Bc 10 cm MIN UNDER BARREL` shows no plus sign between `Bc` and `10`. The figure is an embedded bitmap of about 150 dpi, so a plus could in principle be lost in the raster, but none is visible at native resolution and none was supplied. Recorded as printed, with the ambiguity stated in the draft notes.
- Page 236: the printed equation number `(3.46)` is not returned by native text extraction; it was read from the 288 dpi region render. This affects tooling, not the reading.
- No other glyph, exponent, subscript or cell was left unread.

## Printed discrepancies retained (not corrected)

- `E3.46` prints Field Supporting Strength over Safe Supporting Strength. That matches Equation 3.39 on page 226, where safe supporting strength is field supporting strength divided by the factor of safety, so no discrepancy is claimed and nothing was rearranged.
- `Ep230-1` retains `0.25 D 10cm MIN` (no separator), `0.25 Bc / 10 CM MIN` (literal slash) and `0.125 Bc 10 cm MIN` (no plus). None of these was repaired.

## Files written

- `data/transcriptions/batches/sew-t01/drafts/SEW-2013-A--E3.46.json`
- `data/transcriptions/batches/sew-t01/drafts/SEW-2013-A--Ep159-1.json`
- `data/transcriptions/batches/sew-t01/drafts/SEW-2013-A--Ep230-1.json`
- `data/transcriptions/batches/sew-t01/page-report.json`
- `data/transcriptions/batches/sew-t01/REPORT.md`

Scratch renders under `tmp/pdfs/sew-t01/`: 30 full pages, 3 pinned region PNGs (`final-p159.png`, `final-p230.png`, `final-p236.png`), plus detail crops for the Figure 3.46 callouts, the Figure 3.5 annotation block, the Figure 1.1 percentages and the equation 3.46 region.

Only this batch folder and its scratch render folder were written. No central records, page reviews, coverage or build artifacts changed; the source PDF was opened read-only and nothing was committed.

## Left for the parent

- Distinct second visual pass and verification seals for the three drafts.
- Decision on `Ep230-1` (figure dimension-expression convention) and on a possible `Tp89-1` for the Figure 1.1 percentage box chart.
- Decision on the page 158 dimension callouts, which were deliberately not drafted.
