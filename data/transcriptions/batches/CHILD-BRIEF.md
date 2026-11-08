# Child brief: first-pass visual transcription (draft only)

Repo (cwd): /home/a2ajinkya/.t3/worktrees/omakase-cpheeo/feat-verified-visual-transcriptions
Goal: look at each assigned page IMAGE and transcribe every table and equation (numbered, unnumbered,
vector/scanned, uncaptioned, continuation) exactly as printed. No OCR tools, no paid APIs. Preserve printed
errors verbatim; flag them in `notes` ("Printed as ...; not corrected"). Never invent values. If unreadable, state "unclear".

Rules
- Source PDFs are READ-ONLY. Write ONLY under data/transcriptions/batches/<batch>/ and renders under tmp/pdfs/<batch>/.
- Do NOT touch data/transcriptions/records/, page-reviews.json, coverage.json, data/build/, any tmp/pdfs/author_*.py, or any running server/cloudflared. Don't git commit.
- Render: `uv run python - <<'PY'` using
  from omakase_cpheeo.extract import open_clean; doc=open_clean(PATH); pix=doc[n-1].get_pixmap(dpi=144); pix.save(f"tmp/pdfs/<batch>/page-{n}.png")
  Then actually VIEW each PNG with your image-reading tool. Zoom (crop at 288 dpi via clip=fitz.Rect(bbox)) for small glyphs, powers, subscripts.
- Draft record per target: data/transcriptions/batches/<batch>/drafts/<MANUAL>--<T|E><num or p<page>-<k>>.json
  Template: copy the shape of data/transcriptions/records/SEW-2013-A--E3.10.json (equation) or any SEW-2013-A--T3.*.json (table).
  state "pending"; omit verification.visual_recheck; regions bbox in PDF points [x0,y0,x1,y1] tight around the item (+caption);
  compute render_sha256 = sha256(omakase_cpheeo.transcriptions.region_png(doc, region)).
  Tables: headers, rows (all strings, exact), cell_spans, markdown, notes, title as printed. Unnumbered table ids: T p<page>-<k>.
  Equations: latex, readable, symbols (printed definitions only), applicability, notes. Unnumbered: E p<page>-<k>.
  Skip anything already in data/transcriptions/records/ (check by id).
- Report: data/transcriptions/batches/<batch>/page-report.json = list of {pdf_page, page_label, targets:[ids], no_targets_reason, continuations, unclear, image_viewed:path}.
  EVERY assigned page must appear, including pages with no targets. Plus a short REPORT.md.
- Native PDF text may help locate, but every value must be confirmed against the image.
- create_unit/parent_id: if the table id already exists in data/build/cpheeo.sqlite `units` (baseline indexed table), DO NOT set create_unit or parent_id. Only new/unindexed tables get "create_unit": true plus parent_id = enclosing section unit id.
- Never silently fix spelling: e.g. a printed "CAPICITY" stays "CAPICITY" with a note.
- Equations always need parent_id = the enclosing section unit id (e.g. SEW-2013-A:5.8.1.7.5.2) from `units`.
