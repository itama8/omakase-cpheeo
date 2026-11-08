# WS-2024-B physical pages 70, 72–76, 83, 84, 91, 94 — first-pass visual transcription

Source: `/home/a2ajinkya/Downloads/CPHEEO/Water Supply_2023/Part-B-Manual-Operation-and-Maintenance(5).pdf`,
SHA-256 `1cfd336b3e2928b95cec3899d3e1d15807b5598d78730d6fe3eef381021844e7` (matches `data/transcriptions/sources.json`).
Opened read-only; annotation removal happened in memory through `open_clean` only. No OCR, no native-text reliance,
no delegation, no commit, no writes outside this batch directory and `tmp/pdfs/water-b-t01/`.

Ten annotation-cleaned full-page PNGs were rendered at 144 dpi and each one was viewed with the image tool in this run.

## Counts

| Item | Value |
| --- | --- |
| Pages assigned | 10 |
| Pages inspected | 10 |
| Pages with a table/equation target | 4 (72, 74, 75, 76) |
| Pages with no target | 6 (70, 73, 83, 84, 91, 94) |
| Distinct table ids observed | 2 (`WS-2024-B:T1.1`, `WS-2024-B:T1.2`) |
| Equation ids observed | 0 |
| Unnumbered targets (`T p<page>-<k>`, `E p<page>-<k>`) | 0 |
| New drafts written by this batch | 0 |
| Duplicate ids skipped | 2 (`WS-2024-B:T1.1`, `WS-2024-B:T1.2`) |
| Cross-page continuations observed | 1 (Table 1.2 over pages 74–76) |
| Unclear / unreadable items | 0 |

## Duplicate handling

Both tables on this page set are already drafted, and already rechecked, in the sibling batch:

- `data/transcriptions/batches/water-b-68-79/records/WS-2024-B--T1.1.json` — physical 72, printed 5.
- `data/transcriptions/batches/water-b-68-79/records/WS-2024-B--T1.2.json` — physical 74–76, printed 7–9.
- Recheck evidence: `data/transcriptions/batches/water-b-68-79-recheck/report.json`.

Neither is in `data/transcriptions/records/`, so they are not yet authoritative. I re-read every one of the four
pages from the image and compared the printed structure against those candidates: printed column headings, merged
group rows, row and pair counts, continuation boundaries and source lines all agree, and I propose no correction.
I deliberately did not write second candidates for the same ids under this batch, because two pending candidates for
one id would make parent promotion ambiguous. The existing candidates still need parent-controlled sealing.

## Every-page observations

- Physical 70 / printed 3 — `tmp/pdfs/water-b-t01/page-70.png`. Prose: end of the earlier objective text, 1.1.2 Objective of Operation and Maintenance, 1.2 Operation and Maintenance Scenario. No table, equation or figure. `24×7` appears twice as continuous-service notation, not a multiplication.
- Physical 72 / printed 5 — `page-72.png`. Section 1.3 and the complete Table 1.1 *Summary of Good Practices Drawn from City Case Studies*: two columns, three merged group rows, 13 practice/utility pairs, ADB 2012 source line. Duplicate id skipped (see above). No math or figure.
- Physical 73 / printed 6 — `page-73.png`. Sections 1.4, 1.4.1, 1.4.2; lower two thirds of the page blank. Only a prose reference to Table 1.2. No target.
- Physical 74 / printed 7 — `page-74.png`. Landscape. Table 1.2 *Checklist of O&M Best Practices/Critical Success Factors* begins: five columns with no printed header row, first-column objective groups Increase Utility of Facilities / Decrease total cost / Increase lifetime value. Duplicate id skipped.
- Physical 75 / printed 8 — `page-75.png`. Landscape. Table 1.2 continuation: Extend asset life row finishes, then Reinvest with a life cycle view and the Enable O&M best practice group (Ensure funding, Build capabilities). Duplicate id skipped.
- Physical 76 / printed 9 — `page-76.png`. Landscape. Table 1.2 continuation and end: Build capabilities tail, Reform governance row, then the World Economic Forum 2014 source line. Duplicate id skipped.
- Physical 83 / printed 16 — `page-83.png`. Sections 2.3.8 and 2.4 / 2.4.1, plus Figure 2.1 *Water Utility Focus Areas* (nine overlapping circles with bullet side boxes). Figure unit, no math, outside this batch's target kinds.
- Physical 84 / printed 17 — `page-84.png`. Sections 2.4.2 and 2.4.3 with lettered list (a)–(h), plus Figure 2.2 *Elements of Effective O&M* (four-circle venn). Figure unit, no math.
- Physical 91 / printed 24 — `page-91.png`. Tail of a case-study box from page 90 with `Source: Puri, Odisha`; 2.6.4 Automation (a–e), 2.6.5 Improvements in Water Quality Control, 2.6.6 Water Audit; then the Nagpur PPP case-study box. Both boxes are prose sidebars, not tables.
- Physical 94 / printed 27 — `page-94.png`. Figure 2.3 *Schematic of Information Management System* (labelled schematic, source BWSSB IT Department) then 2.6.10 CMMS prose. Figure unit, no math.

## Printed errors preserved (observations only, nothing corrected)

- Page 70: `breakdown ofequipment` — missing space.
- Page 83: `as per as per Figure 2.1` — the phrase is printed twice.
- Page 84: `drink from tapo all consumers` — `tap to` printed without a space.
- Page 76: source URL printed as `strategic- infrastructure-2014` with a space inside the slug.
- Page 91: item (a) mixes `metre` and `meter` in the same paragraph.

## Concerns and scope gaps

- No new transcription work exists on these ten pages beyond the two duplicate table units. If the parent expected net-new drafts from this page set, the assignment overlaps `water-b-68-79`.
- Figure units on pages 83, 84 and 94 (F2.1, F2.2, F2.3) were not transcribed because the assigned target kinds are table and equation. They carry no mathematical notation, so no figure math was lost.
- Bordered prose inset boxes on page 91 have no rows, columns or captions; serializing them as tables would be an editorial decision for the parent.
- All ranges, percentages and quantities on these pages are prose, not printed formulas (for example 500 MLD, Rs. 95 Crore, 50 Crore, 600 MLD, 490 MLD in the Nagpur box).

## Not done here

Comparison decisions, sealing, promotion into `data/transcriptions/records/`, page-review ledger, coverage, build DB,
server and deployment remain with the parent. This batch claims no verified state and no engineering validation.
