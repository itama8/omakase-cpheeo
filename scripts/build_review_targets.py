"""Build the visual-review target list (union of automated signals).

Derivation (each signal is a prioritisation cue, never verification):
  pdfinspector  - @firecrawl/pdf-inspector 1.25.2 pagesNeedingOcr (0-indexed -> +1)
  images        - embedded_images > 0 in *-pages.json
  vector        - vector_paths >= VECTOR_MIN in *-pages.json
  eqno          - printed equation-number candidates in *-pages.json
  table_unit    - page lies in a table-inventory.json unit range
  math_text     - native text matches maths cues (=, ^, sqrt, operators, Greek)
  table_text    - native text matches 'Table N.N' / dense numeric-row cues
Pages already in page-reviews.json reviewed_pages are excluded; review-scope only.
Pages with no signal form the 'sweep' list for a cheap low-res visual pass.

Usage: uv run python scripts/build_review_targets.py [pdf-inspector-dir]
"""
import json, re, sys
from pathlib import Path

from omakase_cpheeo.corpus import MANUALS, sources_dir
from omakase_cpheeo.extract import open_clean

T = Path('data/transcriptions')
PDFI = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/pdfi')
DET = {'SEW-2013-A': 'det-Seweage_CPHE.json', 'WS-2024-A': 'det-Part-A-Manua.json',
       'WS-2024-B': 'det-Part-B-Manua.json', 'WS-2024-C': 'det-Part-C-Manua.json'}
VECTOR_MIN = 20
MATH = re.compile(r'(\b[A-Za-z]\s*=\s*[\d(A-Za-z√]|√|∑|Σ|∫|±|≤|≥|×|÷|\^|\bsqrt\b|\blog\b|\bln\b|[αβγδεθλμνπρστφω])')
TABLE = re.compile(r'\bTable\s+[A-Z]?\d+(\.\d+)*', re.I)
NUMROW = re.compile(r'^\s*[\d.,\-–\s%]{12,}$', re.M)

reviews = json.loads((T / 'page-reviews.json').read_text())['manuals']
inv = json.loads((T / 'table-inventory.json').read_text())['tables']
out = {'schema_version': 1, 'derivation': __doc__.strip(), 'vector_min': VECTOR_MIN, 'manuals': {}}
for m in MANUALS:
    if m.id not in DET:
        continue
    pages = json.loads((T / f'{m.id}-pages.json').read_text())['pages']
    done = set(reviews.get(m.id, {}).get('reviewed_pages', []))
    det = PDFI / DET[m.id]
    ocr = {p + 1 for p in json.loads(det.read_text()).get('pagesNeedingOcr', [])} if det.exists() else set()
    tpages = {}
    for t in inv:
        if t['manual_id'] == m.id:
            for p in range(t['page_start'], t['page_end'] + 1):
                tpages.setdefault(p, []).append(t['id'])
    doc = open_clean(sources_dir() / m.file)
    targets, sweep = {}, []
    for pg in pages:
        n = pg['pdf_page']
        if pg['scope'] != 'review' or n in done:
            continue
        text = doc[n - 1].get_text()
        sig = []
        if n in ocr: sig.append('pdfinspector')
        if pg['embedded_images']: sig.append('images')
        if pg['vector_paths'] >= VECTOR_MIN: sig.append('vector')
        if pg['equation_number_candidates']: sig.append('eqno')
        if n in tpages: sig.append('table_unit')
        if len(MATH.findall(text)) >= 2: sig.append('math_text')
        if TABLE.search(text) or len(NUMROW.findall(text)) >= 3: sig.append('table_text')
        if sig:
            targets[str(n)] = {'signals': sig, 'tables': tpages.get(n, []), 'eqno': pg['equation_number_candidates']}
        else:
            sweep.append(n)
    out['manuals'][m.id] = {'excluded_reviewed': len(done), 'targets_count': len(targets),
                            'sweep_count': len(sweep), 'targets': targets, 'sweep_pages': sweep}
    print(m.id, 'targets', len(targets), 'sweep', len(sweep))
(T / 'review-targets.json').write_text(json.dumps(out, indent=1) + '\n')
