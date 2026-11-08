# SEW-2013-A physical pages 460-491: first visual reading (batch sew-t06)

25 pending drafts: 24 numbered tables (T5.28 to T5.51) and 1 unnumbered table (Tp483-1). No equations are printed on any assigned page. No record is verified.

Source: `/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf`. SHA-256: `d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`.

## Method

- All 30 assigned pages were rendered at 144 dpi with the production annotation-cleaned loader and actually opened with the image tool. Physical pages 473 and 484 were not assigned and were not read.
- Every table was then read again from a 288-540 dpi crop, band by band. Table 5.29 is inserted sideways as a scanned image, so it was cropped at 4x, rotated 90 degrees and read as two overlapping halves per page.
- No OCR, no paid service, no delegation, no native-text-only reading. Native text was used only to locate items and to read captions and source lines; every value in every draft was confirmed against the image.
- All 25 drafts are `pending` with `create_unit: true`. Region boxes cover the printed caption, the table and its printed footnotes and source lines, and `render_sha256` is computed with `omakase_cpheeo.transcriptions.region_png`.
- Nothing was written outside `data/transcriptions/batches/sew-t06/` and `tmp/pdfs/sew-t06/`. No record, index, build output or server was touched.

## Counts

| Kind | Drafts | Ids |
| --- | --- | --- |
| Numbered table | 24 | T5.28, T5.29, T5.30, T5.31, T5.32, T5.33, T5.34, T5.35, T5.36, T5.37, T5.38, T5.39, T5.40, T5.41, T5.42, T5.43, T5.44, T5.45, T5.46, T5.47, T5.48, T5.49, T5.50, T5.51 |
| Unnumbered table | 1 | Tp483-1 (data grid inside Figure 5.74) |
| Equation | 0 | none printed in this range |

No id in this batch exists in `data/transcriptions/records/`; the existing chapter 5 records stop at T5.11, so nothing was skipped.

Area covered: section 5.18, recent technologies in sewage treatment on printed pages 5-156 to 5-187.

## Page-by-page inspection

| Physical | Printed | Targets | Note |
| --- | --- | --- | --- |
| 460 | 5 - 156 | T5.28 | Table 5.28 with the unboxed "Average of past two years" block |
| 461 | 5 - 157 | none | Running text; Table 5.29 announced overleaf |
| 462 | 5 - 158 | T5.29 | Caption and first three rows; table continues over four more pages |
| 463 | 5 - 159 | T5.29 | Continuation; Type and Objective columns printed empty |
| 464 | 5 - 160 | T5.29 | Continuation; `(N) & (P) Simultaneous removal` printed in the Objective column |
| 465 | 5 - 161 | T5.29 | Continuation; SBR, MBBR, FFASP |
| 466 | 5 - 162 | T5.29 | Final segment; EBB, membrane filtration, MBR; printed note below the table |
| 467 | 5 - 163 | T5.30 | |
| 468 | 5 - 164 | T5.31, T5.32 | |
| 469 | 5 - 165 | none | Running text |
| 470 | 5 - 166 | none | Figures 5.65, 5.66, 5.67 only |
| 471 | 5 - 167 | T5.33 | Two parameter/value pairs side by side |
| 472 | 5 - 168 | T5.34 | Three full-width section rows; asterisked footnote |
| 474 | 5 - 170 | none | Figure 5.68 and running text |
| 475 | 5 - 171 | T5.35 | |
| 476 | 5 - 172 | T5.36 | |
| 477 | 5 - 173 | T5.37 | |
| 478 | 5 - 174 | none | Figures 5.70, 5.71 and running text |
| 479 | 5 - 175 | T5.38 | |
| 480 | 5 - 176 | T5.39 | |
| 481 | 5 - 177 | T5.40, T5.41 | |
| 482 | 5 - 178 | none | Figure 5.73 schematic and running text |
| 483 | 5 - 179 | Tp483-1 | Unnumbered data grid inside Figure 5.74 |
| 485 | 5 - 181 | none | Running text and a three-item plant-data bullet block |
| 486 | 5 - 182 | none | Figure 5.75 only |
| 487 | 5 - 183 | T5.42 | |
| 488 | 5 - 184 | T5.43, T5.44, T5.45 | |
| 489 | 5 - 185 | T5.46, T5.47 | |
| 490 | 5 - 186 | T5.48, T5.49, T5.50 | |
| 491 | 5 - 187 | T5.51 | |

`page-report.json` carries the same page list with image paths, continuation notes and per-page unclear items.

## Printed errors and inconsistencies kept verbatim

Every one of these is recorded in the `notes` of the relevant draft and was **not** corrected:

1. Table 5.29, Step-Feed row: "without a major renovation The unit which consists of ..." — sentence break missing a full stop.
2. Table 5.29, Ion Exchange row: "Clinoptinolite" for clinoptilolite.
3. Table 5.29, Bardenpho row: "Modified Ludzck Ettinger (MLE)".
4. Table 5.29, Ammonia Stripping row: the full stop printed alone on its own line after "threshold limits".
5. Table 5.29 membrane classes (MF 0.08 to 2.0, UF 0.005 to 0.2, NF 0.001 to 0.01, RO 0.0001 to 0.001 microns) against the running text on page 483 (MF 0.1 and 1 micron, UF 0.005 and 0.05 micron, NF around 0.001 micron).
6. Table 5.29, Type and Objective columns printed empty on physical pages 463, 464 and 465.
7. Table 5.30: MLSS range printed as ",810-2,370" with the leading digit missing; Average Influent Flow 50 against a printed Range of 8,287-11,265.
8. Table 5.31: caption printed as "Table 5.31  Performance of Yoshinogawa STP, Japan (FY 2009" with no closing parenthesis.
9. Table 5.32: caption flow 31 MLD against "30 MLD capacity" in the running text of the same page.
10. Table 5.33: "T N - SS loading (kg/kg/day)"; empty second Values cells in five rows.
11. Table 5.34: the asterisk on "2-4 Q*" points to a footnote about mixer energy input; the Combined column prints "2-4 Q" with no asterisk.
12. Table 5.37, 5.41, 5.44, 5.46: "HRT(hours)" printed without a space.
13. Table 5.40 and 5.41: "Anaer obic" printed as a broken word.
14. Table 5.42: "Opening 1 mm," with a trailing comma and nothing after it; "1 Nos." for single units.
15. Table 5.45: "11,600- 14,800" with a space after the hyphen; "2.57-3.5" and "0.26-0.3" with unequal decimals.
16. Table 5-47: caption numbered with a hyphen while neighbours use a full stop; legend prints "s-BOD" against the header "S-BOD"; "TColiform" against "T-coliform" in the legend.
17. Table 5-48 and 5.49: captions numbered with hyphens ("5-48", "5-49", "5-47").
18. Table 5.49: header "Ratio of b) / (a)" with a closing parenthesis that has no opening partner; "replaced (b)" in lower case next to "Installed (a)".
19. Table 5.50: "Flux, (l/m²/day)" with a lower-case l.
20. Tables 5.38, 5-48, 5.50, 5.51: captions name no plant; identification comes only from the running text.

## Unclear items

Nothing on the 30 pages was illegible. These are the readings that are clear as printed but leave something genuinely unresolved:

1. **T5.30** — the printed MLSS range ",810-2,370" has no leading thousands digit, and Average flow 50 contradicts Range 8,287-11,265. Intended values not determinable from this page.
2. **T5.29** — the Type and Objective grouping for the six rows printed on pages 463-465 is not printed; only page 462 (rows 1-3) and the "Secondary" and "Advanced processes" rows carry labels. The record keeps the empty cells and does not invent a grouping.
3. **T5.47** — the row labels "(A)" and "(R)" are never expanded in the table or in the legend. Values are transcribed as printed; the labels' meaning is not printed.
4. **T5.45** — the "(A)" marker is explained only by the "Ferric chloride addition" line below the table, which is itself printed without saying which analyte it applies to.
5. **T5.34** — the asterisk footnote does not read as a note about nitrate recycle, the cell it is attached to.
6. **T5.36** — "Ref 1" and "Ref 2" are both printed as "USEPA, 1987", so the two references cannot be distinguished.
7. **T5.33** — the nested right-hand block leaves five Values cells empty; which parameters they belong to is a layout question, not a printed one.

## Images actually viewed

Full-page 144 dpi renders for all 30 assigned pages under `tmp/pdfs/sew-t06/page-<n>.png`, plus the following crops (all under the same directory):

- page 460: `detail-460-table.png`, `detail-460-below.png`
- page 462-466: `rot-462-r.png` … `rot-466-r.png` (sideways table rotated upright) and `L-462-top.png` … `L-466-bot.png`
- page 467: `d-467-t530.png`
- page 468: `d-468-t531.png`, `d-468-t532-top.png`, `d-468-t532-mid.png`, `d-468-t532-bot.png`, `d-468-t532-bot2.png`
- page 471: `d-471-t533-top.png`, `d-471-t533-bot.png`
- page 472: `d-472-t534-a.png`, `d-472-t534-b.png`, `d-472-t534-c.png`
- page 475: `d-475-t535.png`
- page 476: `d-476-t536.png`
- page 477: `d-477-t537.png`
- page 479: `d-479-t538.png`
- page 480: `d-480-t539.png`
- page 481: `d-481-t540-a.png`, `d-481-t540-b.png`, `d-481-t541.png`
- page 483: `d-483-tab.png`, `d-483-tab2.png`
- page 487: `d-487-t542.png`
- page 488: `d-488-t543-a.png`, `d-488-t543-b.png`, `d-488-t544c.png`, `d-488-t544d.png`, `d-488-t545c.png`
- page 489: `d-489-t546.png`, `d-489-t547a.png`, `d-489-t547b.png`, `d-489-t547c.png`
- page 490: `d-490-t548.png`, `d-490-t549a.png`, `d-490-t549b.png`, `d-490-t549c.png`, `d-490-t550v.png`
- page 491: `d-491-t551a.png`, `d-491-t551b.png`

Region renders for every draft region were also re-viewed after the boxes were tightened: `tmp/pdfs/sew-t06/regions/<id>-p<page>.png`.
