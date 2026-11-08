# SEW-2013-A physical pages 367-414 (sew-t04): first-pass draft transcription

Source: `/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf`, sha256
`d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`, opened read-only through
`open_clean` (annotations deleted in memory only; the file was never saved).

Scope: the 30 assigned physical pages 367, 368, 370, 371, 372, 376-385, 388, 396-399, 403-405,
407, 409-414 (printed labels 5-63 to 5-110). Every page was rendered at 144 dpi
(`tmp/pdfs/sew-t04/page-<n>.png`) and viewed; every table and equation on those pages was then
re-read in 288-900 dpi crops (`tmp/pdfs/sew-t04/c*.png`) before the record was written. No OCR, no
network service, no delegation.

## Counts

| Item | Count |
| --- | --- |
| Pages assigned and viewed | 30 |
| Pages with at least one target | 18 |
| Pages with no target | 12 |
| Numbered equations | 16 (5.26-5.29 and 5.31-5.42; 5.30 is not printed on any assigned page) |
| Unnumbered equation records | 3 (`Ep372-1`, `Ep377-1`, `Ep378-1`) |
| Numbered tables | 6 (5.9, 5.12, 5.13, 5.14, 5.15, 5.16) |
| Unnumbered tables | 0 |
| Draft records written | 25 (19 equations + 6 tables) |
Caption/border items deliberately not turned into records: the labelled grid inside Figure 5.43
(page 399) and the boxed process descriptions inside Figure 5.39 (page 379) are drawing labels, not
tables; the inline factor `(1+0.003 EL)` on page 397 is an inline multiplier in prose, not a
numbered or standalone equation.

## Draft files

`data/transcriptions/batches/sew-t04/drafts/SEW-2013-A--<id>.json`, all `state: "pending"`, each
with one `regions[]` entry (page, printed label, tight bbox in PDF points, `render_sha256` computed
with `omakase_cpheeo.transcriptions.region_png`) and only a `verification.transcription` note. No
`verification.visual_recheck` was written, no `content_sha256`, nothing sealed.

Per page:

- 367 / 5-63: E5.26, E5.27
- 368 / 5-64: T5.9
- 370 / 5-66: E5.28
- 372 / 5-68: E5.29, Ep372-1
- 376 / 5-72: E5.31
- 377 / 5-73: Ep377-1
- 378 / 5-74: Ep378-1
- 380 / 5-76: T5.12
- 381 / 5-77: E5.32
- 383 / 5-79: T5.13
- 384 / 5-80: E5.33, E5.34
- 385 / 5-81: E5.35
- 397 / 5-93: T5.14, E5.36
- 398 / 5-94: E5.37, E5.38
- 399 / 5-95: E5.39, E5.40
- 407 / 5-103: T5.15
- 410 / 5-106: T5.16
- 412 / 5-108: E5.41, E5.42

Pages with no target, with the reason recorded in `page-report.json`: 371, 379, 382, 388, 396, 403,
404, 405, 409, 411, 413, 414.

## Printed oddities preserved (not corrected)

- 367: kd = 0.06/d in the prose, k = 0.06d-1 in the Figure 5.37 caption.
- 380, T5.12 row 4: "BOO removal efficiency %" (letter O for D); row 7 Extended Aeration cell
  prints "0. 6" with a space; row 3 Extended Aeration cell is blank; row 9 prints "9" without a
  full stop while rows 1-8 print "1." to "8.".
- 381, E5.32: exponents printed as 1/2d, a/2d, −a/2d (not 1/(2d)).
- 384, E5.34: equation prints lower-case theta, the definition list prints capital Theta; TL has no
  printed definition; the f-definition ends with a stray "and".
- 397, E5.36: L printed with a lower-case o subscript; the Lo definition ends with a stray "and".
- 398, E5.37/E5.38: K subscript printed as an italic lower-case l, not the digit 1.
- 399, E5.40: definition prints "K b(T)" and "K b(20)" with a space.
- 410, T5.16: "Mg(OH) 2" with a space before the subscript 2 in two places; "2341+4313=6654" with no
  spaces; "2597=" with no space; the Precipitates row breaks the line after a bare "92" and then
  prints "SiO2 = 24457 mg/l".
- 412, E5.41: the coefficient of H3PO4 is set as a subscript immediately after the plus sign
  ("+ 2H3PO4" printed as "+ ₂H₃PO₄").
- 412, E5.42: ionic charges printed as plain hyphens after closed-up subscripts; "8 H2O" with a
  space.
- 383, T5.13: title prints a space before the en dash ("Length –Width"); third row prints "- do-".

## Unclear or needing a second reader

1. 410, T5.16 Precipitates row: the printed line ends "... BaSO4 = 11399 (+) 92" and continues
   "SiO2 = 24457 mg/l". The role of the bare 92 is ambiguous as printed (the arithmetic
   9370 + 3596 + 11399 + 92 = 24457 does work out), so nothing was inferred or corrected.
2. 410, T5.16: the table prints no column-header row; the seven headers in the record are
   transcriber-supplied structural labels, flagged in `notes`.
3. 381, E5.32: the printed inline line "a = √1 + 4Kθd" was read with the radical covering the whole
   `1 + 4Kθd` after an 8x zoom of the radical bar; a second reader should confirm the bar extent.
4. 376, E5.31: the printed "where," list stops after QR, so Q, X and Xs are undefined on the page;
   their meanings come from page 377 prose, not from a printed definition list.
5. 372, Ep372-1: printed "Yobs" is subscripted in the ΔX row but not on the Yobs row; the record
   keeps both forms.
6. 368, T5.9: the "Flow Regime" group heading has no cell of its own in the five-column record and
   is carried in `notes` instead.
7. Numbering gap: Equation (5.30) is not printed on any assigned page (the sequence jumps 5.29 to
   5.31); it presumably sits on an unassigned page, but no assumption was made about its content.

## Boundaries honoured

Only `data/transcriptions/batches/sew-t04/` and `tmp/pdfs/sew-t04/` were written. `data/transcriptions/records/`,
`page-reviews.json`, `coverage.json`, `data/build/`, the source PDF, other batches and any running
server were left untouched. Nothing was committed. `tmp/pdfs/sew-t04/build_drafts.py` and
`build_report.py` are the throwaway generators used for these drafts and are not part of the repo
pipeline.
