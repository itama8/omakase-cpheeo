# WS-2024-A physical pages 86–97 (batch water-a-t01): first-reading handoff

Source SHA-256: `b60f2fb548357aec676b18ef31e3b37fb0e5e8a1aec8f886880b951113848b0a`, re-hashed from the source file and equal to `sources.json`. Assigned pages only: 86, 87, 88, 91, 92, 93, 94, 95, 96, 97. Pages 89, 90 and 98+ are outside this batch and were not read.

Every assigned page was rendered annotation-free at 144 dpi (`tmp/pdfs/water-a-t01/page-<n>.png`) and viewed as an image; each table was then re-read from a 3x clipped crop (`p91-table1.1-zoom.png`, `p92-table1.1-cont-zoom.png`, `p95-table1.2-zoom.png`, `p96-table1.3-zoom.png`). No OCR was used, and native text was used only to locate geometry, never as a source of values. Proof-of-region crops for each record were rendered from the pinned bboxes (`T1.1-region-p91.png`, `T1.1-region-p92.png`, `T1.2-region-p95.png`, `T1.2-region-p96.png`, `T1.3-region-p96.png`).

## Deliverables

Three pending, unsealed records in `drafts/`:

| Record | Physical / printed | Shape |
| --- | --- | --- |
| `WS-2024-A--T1.1.json` | 91–92 / 6–7 | 3 columns, 13 data rows; rows 12–13 on the second page under a reprinted header row |
| `WS-2024-A--T1.2.json` | 95 / 10, source line 96 / 11 | 4 columns, 9 data rows; source line is a second region |
| `WS-2024-A--T1.3.json` | 96 / 11 | 3 columns, 7 rows plus a Total row |

All three table handles (`WS-2024-A:T1.1`, `T1.2`, `T1.3`) already exist in the read-only baseline `units` table, so no record sets `create_unit` or `parent_id` and no new unit was proposed.

Also in this folder: `page-report.json` (all ten assigned pages, including the six with no target), `validation.json` (shape, cell-grid, source-hash and region-hash reproduction), and the two scratch scripts `tmp/pdfs/water-a-t01/pass_a.py`, `pass_b.py`.

## Counts

- Assigned pages inspected: 10.
- Pages with a target: 4 (91, 92, 95, 96). Pages with no target: 6 (86, 87, 88, 93, 94, 97).
- Tables drafted: 3 (all captioned and numbered; no uncaptioned table was found).
- Equations drafted: 0. No numbered or unnumbered equation, displayed formula, or symbolic ratio is printed on these pages. The `math_text` signals on 88, 93, 94 and 97 are inline prose quantities and the 24×7 service notation, which are reported per page instead of being drafted as equations.
- Continuations: 1 table continuation (T1.1, p91→p92) and 1 cross-page table source line (T1.2, p95→p96).

## Uncertain and printed-error concerns for the parent's comparison

1. **T1.2 `135*`** — the asterisk on the targeted benchmark for per-capita supply has no printed footnote, key or explanation on pages 95 or 96. Kept verbatim; nothing inferred. The next page separately states 150 LPCD as the target for cities above 10 lakhs population (IS 1172:1993), which does not reconcile with the table.
2. **Header forms differ across the three tables** — T1.1 prints a stacked bare `S` / `N` (no periods, no "No."), T1.2 prints `S. N.`, T1.3 prints `SN`. Each is transcribed as printed; do not normalise them.
3. **Flattened two-line headers** — T1.2 `Targeted Benchmark` and T1.3 `Quantity (LPCD)` are printed on two lines and flattened with one space. Flagged in `notes` so the parent can judge whether `cell_spans`/header handling needs a different convention.
4. **T1.3 Total row** — the serial cell is printed empty and the column rules continue through the row, so no merge was recorded; the empty cell is an empty string, not a missing value.
5. **Figure 1.1 legend (p86)** — printed bands run Low (<10%), Low to Medium (10-20%), Medium to High (20-40%), High (40-60%), Extremely High (>80%); the 60–80% band is printed as `>80%` only. Figure-internal, left to the figure pipeline, recorded here because it looks like an unfilled range.
6. **Acronym variance (p97)** — section heading prints `IUWRM`, the sentence beneath prints `IURWM system`. Prose only; nothing transcribed, nothing corrected.
7. **Figure-level, not transcribed** — Figure 1.2 pie labels (62/9/12/9/2/4/2, totalling 100), Figures 1.4/1.5 schematics and Figure 1.3 panels (a)–(d) are drawings with captions and no tabular or formula content; they were inspected and referred to the figure pipeline rather than drafted as tables.

## Scope gaps

- Pages 89–90 (end of section 1.4.1 through 1.4.3) and 98 onward are not part of this batch; anything on them is unread here.
- Nothing was sealed, verified, integrated, or written to `records/`, the review ledger, coverage, the build DB, the server or the tunnel, and no commits were made. The source PDF was opened read-only and never saved. A distinct second visual comparison, all corrections, and any verification decision belong to the parent.
