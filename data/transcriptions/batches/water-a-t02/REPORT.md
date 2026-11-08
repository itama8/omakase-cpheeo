# WS-2024-A physical pages 98–110 (batch water-a-t02): first-reading handoff

Source SHA-256: `b60f2fb548357aec676b18ef31e3b37fb0e5e8a1aec8f886880b951113848b0a`, re-hashed from the source file on disk and equal to `sources.json`. File:
`/home/a2ajinkya/Downloads/CPHEEO/Water Supply_2023/Part-A-Manual-Engineering-Planning-Design-and-Implementation(3).pdf` (read-only, never saved).

Assigned pages only: 98, 99, 100, 103, 104, 105, 106, 107, 109, 110. Pages 101, 102, 108 and 111 are outside the assigned set and were not read as targets; 101, 108 and 111 were each rendered and viewed exactly once to close a continuation question (see below).

Every assigned page was rendered annotation-free (`open_clean`) at 144 dpi to `tmp/pdfs/water-a-t02/page-<n>.png` and viewed as an image. Small glyphs, headers and the two-line cells were re-read from 3x–4x clipped crops (`p106-iuwrm-zoom.png`, `p109-table2.1-zoom.png`, `p110-table2.1-cont-zoom.png`). No OCR was used; native text served only to locate geometry (rule coordinates, caption lines), never as a source of values. Both evidence regions were re-rendered from their pinned bboxes (`T2.1-region-p109.png`, `T2.1-region-p110.png`) and compared against the draft.

## Deliverables

One pending, unsealed record in `drafts/`:

| Record | Physical / printed | Shape |
| --- | --- | --- |
| `WS-2024-A--T2.1.json` | 109–110 / 24–25 | 3 columns, 9 data rows; header + serials 1–6 on page 109, serials 7–9 on page 110 with no reprinted header |

The table handle `WS-2024-A:T2.1` already exists in the read-only baseline `units` table (`page_start` 109, `page_end` 110, parent `2.8.1.1`), so the record sets neither `create_unit` nor `parent_id` and no new unit is proposed. The indexed `table_markdown` for that unit agrees cell-for-cell with the visual reading; the reading was taken from the image, not from that text.

Also in this folder: `page-report.json` (all ten assigned pages, including the eight with no target), `validation.json` (source hash, page coverage, image paths, cell grid, markdown and region-hash reproduction), and the scratch helper `tmp/pdfs/water-a-t02/report_tools.py`.

## Counts

- Assigned pages inspected: 10 (98, 99, 100, 103, 104, 105, 106, 107, 109, 110).
- Pages with a target: 2 (109 and 110, both the same table). Pages with no target: 8 (98, 99, 100, 103, 104, 105, 106, 107); no assigned page was left unread.
- Tables drafted: 1 (`T2.1`, a two-page continuation).
- Equations drafted: 0. No numbered or unnumbered equation is typeset anywhere on these pages. Every candidate signal is prose: NRW "the difference of the quantity of water supplied and water billed" (p106), the top-down/bottom-up audit descriptions (p106), "Distance is calculated by multiplying the time taken to cover a certain distance by velocity" (p107), and the inline percentages (95%, 100%, 50%, 31%, 15%, 10%) on 103–110. Writing these as formulas would invent notation the manual does not print, so none was drafted.
- Continuations: 1 in-scope table continuation (T2.1, p109→p110). 3 boundary checks outside the assigned set (below).

## Continuation checks (pages outside the assigned set, viewed once, no record written)

1. **p100 → 101.** The Part A chapter listing runs off the foot of p100; p101 was viewed and only continues the same listing (Part B Chapter 1–13, then Part C: Management chapters 1–9). Nothing tabular was found on p101 and no record was written.
2. **p107 → 108.** p107 ends inside an a)–c) list; p108 was viewed and only continues that list (d)–g) LIDAR, Drones, DGPS-RTK, CORS) into 2.7.1.2 and 2.7.1.3. No table crosses.
3. **p110 → 111.** p110 ends in prose (2.8.1.3); p111 was viewed and only continues that prose into 2.8.1.4–2.8.1.6. No table crosses.

## Judgement calls the parent should confirm

1. **p100/p101 chapter listing is not drafted as a table.** It is a hanging-indent `Chapter N: title` list with no caption, no table number, no header row and no rules, and the baseline index holds no table unit at section 1.11. The full text of both halves is recorded verbatim in `page-report.json` observations (p100 and the p101 continuation note) so it can be promoted to `T p100-1` if the inventory convention differs. This is the only page in the batch where a structured multi-column block was deliberately not recorded as a table.
2. **Figure keys are not drafted as tables.** p103 prints an inline italic key under Figure 2.1 (`ESR: Elevated Service Reservoir; MBR: Master Balancing Reservoir; WTP: Water Treatment Plant`) and p98/p104/p107 print box diagrams (`F1.6`, `F1.7`, `F2.1`, `F2.2`, `F2.3`). These are figure-internal, uncaptioned and unruled, and were left to the figure pipeline, matching how batch `water-a-t01` handled the Figure 1.1 legend.
3. **T2.1 row 9 is one cell, not two.** `Efficiency in collection of water supply-` / `related charges` is set on two justified lines inside one cell; the trailing hyphen belongs to the printed compound. Recorded as `Efficiency in collection of water supply-related charges`, `cell_spans` empty. No row in this table has a merge.
4. **Two-line header flattened.** `Targeted` / `Benchmark` is printed on two lines and flattened with a single space, as batch `water-a-t01` did for `Targeted Benchmark` and `Quantity (LPCD)`.
5. **Serial-header forms differ between tables.** T2.1 prints `S. No.` with periods (T1.1 prints a bare stacked `S`/`N`, T1.3 prints `SN`). Each is transcribed as printed; do not normalise.

## Printed-error and consistency concerns (all kept verbatim, nothing corrected)

1. **Acronym `IUWRM` vs `IURWM`.** p104 (Figure 2.2 box), p106 (2.6) and p110 (2.8.1.3) print `IUWRM`; page 97 prose prints `IURWM`; p105 prints `(IUWRM)` in 2.6. The p106 form was confirmed on a 4x crop. Not corrected; the parent may want one manual-wide note rather than per-record notes, since no record here carries it.
2. **`135 LPCD` (T2.1 row 2) vs `135*` (T1.2, p95).** The asterisk on page 95 has no printed footnote; T2.1 prints the same 135 without any mark. Both are printed; nothing inferred.
3. **`in the Table 2.1`** — the sentence above the table prints the definite article (`are shown in the Table 2.1`). Recorded in the record notes; the sentence is not part of the table.
4. **`Investigation` vs `INVESTIGATIONS`** — p100's Chapter 2 listing line prints the singular, while the Chapter 2 running title prints the plural. List only, no record.
5. **p107 heading `Preparatory Phase – Survey & Investigation`** uses an en dash between "Phase" and "Survey"; p109's `2.8 Preparatory Phase - Planning & Design` uses a hyphen. Both as printed.

## Scope gaps

- Pages 101, 102, 108 and 111 are not batch targets; anything on them beyond the three continuation checks above is unread.
- Annexures referenced from these pages (2.1, 2.2, 2.3, 2.4, 2.5) and the Tables 1–5 of IS 10500:2012 cited on p111 were not read.
- Every equation-like statement on this page range is prose, so this batch yields no equation draft at all. If the parent expects equations from these pages, the gap is a reading disagreement rather than an omission: `page-report.json` records the exact wording of each candidate.
- Nothing was sealed, verified, integrated, or written to `records/`, the review ledger, coverage, the build DB, the server or the tunnel; no commits were made. No sibling pending draft matches these ids or pages (`WS-2024-A:T2.1` was absent from `records/` and from every other batch's `drafts/`, so no parent promotion is requested from another batch). A distinct second visual comparison and any verification decision belong to the parent.
