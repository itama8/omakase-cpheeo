# SEW-2013-A physical pages 818-826: first visual reading

Status: feasible first-pass authoring completed; all candidates remain **pending**. No separate second visual inspection, verification digest, application, central-ledger update, DB write, deployment or commit was performed. No OCR or paid service was used. Source PDF and SQLite were opened read-only. This report supersedes no central coverage ledger and relies on no Scout claims.

## Deliverables

- 28 candidate JSON records: 22 equations (all unnumbered, `Ep<physical-page>-<sequence>` service locators) and 6 tables.
- Four tables have existing indexed targets: `TA2.2-1`, `TA2.2-2`, `TA3.1-1`, `TA3.1-2`.
- Two tables (`Tp822-1`, `Tp825-1`) are **draft only**, with no existing target. They cannot currently be applied. Proposed IDs are service locators, not printed table numbers. Architecture belongs to the parent task.
- `manifest.json` lists every candidate filename and the actual source PDF SHA-256. Every candidate contains exact source and annotation-cleaned 144-dpi region PNG hashes. Generated candidate crops are in the assigned scratch folder; generating them is not a claim of separately viewing them.
- Scratch authoring script: `tmp/pdfs/sew-appendix-818-826/author_batch.py`. It writes only this batch and its scratch folder and reads SQLite via `mode=ro`. It imports no old batch author.

## Per-page findings and images actually viewed

Paths below are relative to the worktree. Every `page-N.png` is a full-page render and was directly opened with the image-viewing tool. Selected detail views were part of the same first reading, not a second pass. No page was declared complete from native text.

| Physical / printed page | Visually found targets and disposition | Source images actually viewed |
| --- | --- | --- |
| 818 / A - 47 | Table A2.2-1 (9 body rows including Total/Average); arithmetic increase/subtraction and per-decade division (`Ep818-1`); 2001 arithmetic population chain (`Ep818-2`); 2016 arithmetic population chain (`Ep818-3`). All authored. Table 1931 increment prints 15,873, although later growth calculation uses 4,337. No continuation of the table. | `tmp/pdfs/sew-appendix-818-826/page-818.png` |
| 819 / A - 48 | Six decadal growth ratios (`Ep819-1`); sixth-root geometric mean and repeated rg = 0.2442 (`Ep819-2`); geometric 2001 and 2016 population chains (`Ep819-3`, `Ep819-4`); Table A2.2-2 (9 body rows including Total/Average); average-row division expressions also captured as `Ep819-5`. All authored. Incremental method continues to page 820. | `tmp/pdfs/sew-appendix-818-826/page-819.png`; `tmp/pdfs/sew-appendix-818-826/detail-819.png` |
| 820 / A - 49 | Printed general population projection formula (`Ep820-1`), using Y in BOTH terms; 2001 and 2016 incremental calculation chains (`Ep820-2`, `Ep820-3`); graphical projection year/population pairs (`Ep820-4`). Figure A2.2-1 semi-log graph inspected: axes population in thousands vs years, observed points and projection guides. No equation inside graph; continuous plot not digitized. Text says figure on following page although graph is on same page; no repair. | `tmp/pdfs/sew-appendix-818-826/page-820.png`; `tmp/pdfs/sew-appendix-818-826/detail-820.png` |
| 821 / A - 50 | Appendix A3.1 basic-data values and symbolic inlet times (`Ep821-1`). Figure A3.1-1 area/street plan inspected. Visible area labels 1-15 carry hectare values: 1.7, 2.1, 1.2, 1.3, 1.7, 2.2, 2.3, 2.4, 5.6, 4.2, 5, 4.8, 6.3, 3.7, 2.9 respectively. These are diagram labels, not inferred table cells. Plan geometry/manhole marks remain image evidence; no formula inside plan. Solution continues on page 822. | `tmp/pdfs/sew-appendix-818-826/page-821.png` |
| 822 / A - 51 | Q = 10 C i A with definitions/units (`Ep822-1`); unindexed six-pair intensity-duration interpolation table (`Tp822-1`, blocked draft); i = a/t^n with definitions (`Ep822-2`); inline a = 160, n = 0.4, i = 160/t^0.4 (`Ep822-3`); Table A3.1-1 with 13 duration/intensity pairs. All authored. Table first row t_min and second-row expression retained. Item v begins at bottom and continues on page 823; no extra table continuation. | `tmp/pdfs/sew-appendix-818-826/page-822.png` |
| 823 / A - 52 | Continuation of item v, 10 C i vs t and runoff units (`Ep823-1`); weighted t_c fraction and printed A1/A2 definitions (`Ep823-2`); inline 70/(60 × 1.0) = 1.17 min (`Ep823-3`); Col.20 = Col.19 × Col.16 (`Ep823-4`). All authored. Table A3.1-2 introduced/described here, actual cell grid on page 824; column 22 description continues via page 825 prose. Page says time of flow in line 1; preserved. | `tmp/pdfs/sew-appendix-818-826/page-823.png` |
| 824 / A - 53 | Full sideways Table A3.1-2: 23 columns × 11 body rows, all cells authored with flattened multi-level headers; source column numbers documented. Header t_c = t_i + t_f also authored (`Ep824-1`). No continuation of the grid; surrounding explanatory prose continues on page 825. Source street blanks retained. | `tmp/pdfs/sew-appendix-818-826/page-824.png`; `tmp/pdfs/sew-appendix-818-826/page-824-rotated.png` |
| 825 / A - 54 | Continuation of design explanation: line 1/3/6/9 invert values respectively 37.400, 36.700, 38.000, 36.000. Col.23 = Col.22 - Col.20 (`Ep825-1`). Figure A3.1-2 street/contour plan inspected (contours 34.0-38.0, manholes and pump house). Figure A3.1-3 log-log intensity-duration graph inspected; embedded six-pair table authored as `Tp825-1`, blocked draft. Graph caption and one-year-storm context retained in report; continuous line not digitized. Prose's 36.000 for line 9 conflicts with table's 36.800; no repair. | `tmp/pdfs/sew-appendix-818-826/page-825.png`; `tmp/pdfs/sew-appendix-818-826/detail-825.png` |
| 826 / A - 55 | Figures A3.1-4, A3.1-5 and A3.1-6 fill the page: intensity-duration one-year-storm curve; runoff coefficient vs duration; runoff-rate vs duration curves labelled 100% impervious, 50% impervious, 30% impervious, 100% pervious. No new equation, cell table or mathematical expression to author was found beyond axis labels and numerical tick marks. Continuous curves/points are not digitized or interpolated. Figure A3.1-5 caption prints “After horner area rectangle”. | `tmp/pdfs/sew-appendix-818-826/page-826.png` |

## Unknowns, limits and unfinished work

- All 28 candidates require an actual separate second inspection before any verification sealing. First-reading enlargement is not such an inspection.
- Both unindexed-table drafts require parent architecture work before application. They intentionally have no invented existing target.
- Graph curves and plan geometry remain image evidence rather than numerical transcriptions. No graph-interpolated population, runoff coefficient, area or intensity value was invented. Figure A3.1-5 curves have no visible individual identifiers at this resolution; their engineering meaning beyond the visible axes/caption is not asserted.
- No unreadable formula glyph remains asserted as a guessed value. Multi-line expressions are grouped by logical calculation; their constituent equalities appear in the readable text and LaTeX. Header/caption context and basic-data assignments are accounted for.
- Source anomalies retained: repeated Y in page 820 projection formula; 1931 table increment discrepancy; line 9 invert prose/table discrepancy; printed precision and blanks in Table A3.1-2. The trailing dot on line 7 capacity is retained as `70.` and deserves attention in the second inspection.
- Table merge labels for Total/Average are explicitly described in notes; blank companion cells are not missing numerical data. Hierarchical storm-sewer headers are flattened; no numerical blank filled by inference.
- Assigned page boundary ends at 826. No claim is made about targets or continuations outside pages 818-826.

## Validation

`validation.json` records structural checks, exact re-render hash checks and read-only target existence checks. These are mechanical checks only; they establish neither second-pass fidelity nor engineering correctness. No apply/refresh command was run.
