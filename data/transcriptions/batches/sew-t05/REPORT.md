# SEW-2013-A physical pages 415-459 (batch sew-t05): first visual reading

14 pending drafts: 13 tables (11 numbered, 2 unnumbered) and 1 numbered equation. No draft is verified.

Source: `/home/a2ajinkya/Downloads/CPHEEO/Seweage CPHEEO.pdf`. SHA-256: `d6bcbe8a2dcf2b3af6377d22d39fe706ed874937d9b384a3e7e3c26d93333288`.

All 30 assigned page images were rendered from the annotation-cleaned PDF at 144 dpi and opened with the image-viewing tool. Sideways (landscape-printed) pages were re-rendered upright before reading. Every table cell, dash, blank, power and footnote was read from a 288-300 dpi crop; native PDF text was used only to locate items and to find section headings, never as a source of values. No OCR, no paid service, no delegation.

Pages 421, 423, 426, 427, 430, 438, 439, 441-443, 449, 451-453, 456 were not assigned and were not inspected.

## Targets found

| id | page | printed item |
| --- | --- | --- |
| `SEW-2013-A:T5.17` | 416 | Table 5.17 Variation of data of Ganga River during 1986-2008 |
| `SEW-2013-A:T5.18` | 417 | Table 5.18, upper Observed Class panel |
| `SEW-2013-A:Tp417-1` | 417 | Table 5.18, lower Critical Parameter panel (unnumbered panel) |
| `SEW-2013-A:Tp418-1` | 418, 419 | boxed 70-entry location key of Figure 5.51 and Figure 5.52 (unnumbered) |
| `SEW-2013-A:T5.19` | 422 | Table 5.19 Technical factors and feasibility considerations in disinfectant choice |
| `SEW-2013-A:T5.20` | 424 | Table 5.20 Recommended Guidelines for Treated Sewage ... |
| `SEW-2013-A:T5.21` | 429 | Table 5.21 Requirement of power for different capacities of STP |
| `SEW-2013-A:T5.22` | 432 | Table 5.22 General motor ratings for various voltage ranges |
| `SEW-2013-A:T5.23` | 432 | Table 5.23 Protective enclosures and types of environment |
| `SEW-2013-A:T5.24` | 433 | Table 5.24 Margins for motor-ratings |
| `SEW-2013-A:T5.25` | 435 | Table 5.25 Guidelines for starters for squirrel-cage motors |
| `SEW-2013-A:E5.43` | 436 | equation (5.43) N = 120xf/P with its f / P definitions |
| `SEW-2013-A:T5.26` | 437 | Table 5.26 Types of cables for different voltages |
| `SEW-2013-A:T5.27` | 455 | Table 5.27 Piping Materials in Sewerage and Sewage Treatment |

None of these ids exists in `data/transcriptions/records/`; every id above was checked against that directory before authoring.

## Judgement calls

- **Table 5.18 is one printed grid with two panels.** The upper panel (Locations, Desired Class, six Observed Class year columns) and the lower panel (Locations, six Critical Parameter year columns) have different column counts, so they are authored as two records rather than one grid with 14 columns and many empty cells. This follows the existing part-splitting precedent of `TA2.2-1`/`TA2.2-2`. The whole-table region is attached to `T5.18`; the lower panel has its own tight region.
- **The Figure 5.51/5.52 location key is transcribed as an unnumbered table.** It is a boxed, ruled grid of 70 numbered locations printed under both charts. It is not a numbered manual table, so it takes the `Tp418-1` service-locator id, and both page regions are attached to one record because the two printings are identical. A reviewer who decides a chart axis key is out of scope can drop this one record without touching any other.
- **Figure 5.53 (page 425), Figure 5.54 (page 440), Figure 5.61 (page 457) and the pie charts on 459 were not turned into records.** They are flow/schematic diagrams, a symbol legend, a boxed algorithm and labelled pie slices; none prints a formula or a data grid. Converting their arrows or slice labels into equations would be invention.
- **Inline chemistry and inline ranges are not equations.** The de-chlorination formulae on 420, the 4 to 20 mA signal on 447/448 and the 3% cable voltage-drop rule on 436 are running text.
- **Specifically flat-blank cells are kept as empty strings,** never as zero or NA: Varanasi U/S 1997-2008 block on 417 (2000 cell), the Critical Parameter panel blanks, the Chemical Process Piping concentration cell on 455, the Soft Start torque ratio on 435, and the 3.3/6.6/11 KV supply cells on 432.

## Printed anomalies retained (not corrected)

- Table 5.18: the 2008* column has an asterisk with no asterisk footnote printed on the page. Allahabad U/S and D/S print `CF,BOD` where other rows print `BOD,CF`.
- Table 5.17: row 7 Kanpur D/S prints 1993 (a) = 5.2 and 1993 (b) = 24.5, unlike the neighbouring rows.
- Table 5.27: the Influent row prints `CL` and many material lists print `HP`, while the printed legend defines `CI - Cast Iron` and `P - High Density Polyethylene`. The Primary solids row prints `0.2 to1` with no space.
- Table 5.26: rows are numbered 1., 2., 4, 5; there is no row 3. Row 5 prints an en dash in `1 phase – 230 V` where row 1 prints hyphens.
- Table 5.23: header printed as `Enclo-` / `-sure` / `type` on three lines; `IP.11`-`IP.55` carry a point but `IP 68` does not; the fourth description ends `- limited ingress.` without `permitted`.
- Equation (5.43): `N` is not defined in the printed symbol list, and the definition of `f` ends with the conjunction `and`.
- Figure 5.53 on 425 captions both Case 2 and Case 3 as `Bardenpho process with Chlorination`, although Case 3 shows Anaerobic/Anoxic/Oxic tanks.

## Unclear or unresolved

- No glyph on any assigned page was unreadable, so no draft is marked `unclear`.
- Two scope questions are left to the parent rather than settled silently: whether the Figure 5.51/5.52 chart location key counts as a table (`Tp418-1`), and whether a two-panel printed table should be one record or two (`T5.18` + `Tp417-1`).
- `parent_id` is set only where the containing section number is printed or referred to on the assigned pages: 5.12.2.8 (T5.21), 5.12.3.5 (T5.22), 5.12.3.6 (T5.23), 5.12.3.9 (T5.24), 5.12.3.13 (T5.25), 5.12.3.15 (E5.43), 5.12.3.16 (T5.26), 5.15.5 (T5.27). For Tables 5.17-5.20 and the two unnumbered tables the enclosing section heading is not printed on the assigned pages, so `parent_id` is null instead of guessed.
- `create_unit` is true for the table drafts. Unit existence in the built index was **not** checked, because `data/build/` is out of scope for this batch; the parent must confirm that these table units do not already exist before applying.

## Checks performed

- Every draft: `schema_version` 1, `state` "pending", no `verification.visual_recheck`, `source_sha256` matches the assigned PDF digest, every region `bbox` inside the page and inside the printed item, and `render_sha256` recomputed with the production `region_png` renderer and matched.
- Every table draft: all rows are the same width as `headers`, every cell is a string, no cell contains an embedded newline, and `markdown` regenerates exactly from cells using the production formatting rule.
- Every table region was re-rendered and viewed to confirm the crop actually contains the whole item plus its caption, key and source line; two first-pass boxes were widened after that check (Table 5.21 notes, Table 5.18 lower panel).
- These are structural checks only. They do not establish visual fidelity, and no second visual pass was performed.

## Files

Drafts, `data/transcriptions/batches/sew-t05/drafts/`:

- `SEW-2013-A--T5.17.json`, `SEW-2013-A--T5.18.json`, `SEW-2013-A--Tp417-1.json`,
  `SEW-2013-A--Tp418-1.json`, `SEW-2013-A--T5.19.json`, `SEW-2013-A--T5.20.json`,
  `SEW-2013-A--T5.21.json`, `SEW-2013-A--T5.22.json`, `SEW-2013-A--T5.23.json`,
  `SEW-2013-A--T5.24.json`, `SEW-2013-A--T5.25.json`, `SEW-2013-A--T5.26.json`,
  `SEW-2013-A--T5.27.json`, `SEW-2013-A--E5.43.json`

Reports: `page-report.json` (all 30 assigned pages, including pages with no target), `validation.json`, this `REPORT.md`.

Only this batch folder and `tmp/pdfs/sew-t05/` were written. No central record, ledger, coverage file, build output, deployment, server, tunnel or Git state was changed.
