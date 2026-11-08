# Child brief: selected visual targets only

Current policy: `data/transcriptions/work-policy.json`. The user replaced the whole-page sweep with small batches. Historical page-range assignments are stopped.

- Work on at most five explicitly selected table/equation targets, one active batch at a time. Do not fan out across manuals or inspect every page.
- Choose target IDs from the existing inventory, saved pending drafts, extraction problems or concrete retrieval needs. View their source-region images and necessary continuation/context only. Do not turn a target into a chapter/page sweep.
- Source PDFs are read-only. Use `open_clean` for annotation-cleaned renders and production `region_png` for evidence hashes. Actually view every target crop; zoom uncertain glyphs. No OCR or invented values.
- Write only under the assigned `data/transcriptions/batches/<batch>/` and `tmp/pdfs/<batch>/`. No central records, review ledger, coverage, build DB, server, tunnel, commits or further delegation.
- Follow existing record schema: pending state, manual/unit/source hash, region page/printed label/bbox/render hash, exact string cells and Markdown, or equation LaTeX/readable/symbols. Preserve printed errors with notes. Unreadable values remain explicitly unclear.
- Join wrapped cell text with spaces, preserving bullet markers and printed punctuation. Markdown must exactly match structured cells.
- Equations need the enclosing section parent_id. Baseline table IDs must not set create_unit; only truly new tables need create_unit and parent_id. Never infer mathematical notation from prose.
- Explicit equations, inequalities and other mathematical expressions within figures are valid targets; they do not require transcribing the rest of the figure.
- Existing pending candidates may be reused after visual comparison; report their paths and corrections. They are not verified merely because they exist.
- Save progress after each target. Report selected IDs, viewed evidence, continuations, corrections and unresolved concerns. Do not claim the whole page was reviewed when only a crop was checked.
- The parent performs a distinct visual recheck, seals the digest and integrates; do not set verified or visual_recheck yourself.
