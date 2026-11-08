"""Inventory EVERY source page, including pages without detected table/image units.

Signals prioritize review; they do not prove coverage or classify mathematical content.
Run after ingestion. The versioned page ledger never equates detection with visual review.
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from omakase_cpheeo.corpus import MANUALS, sources_dir
from omakase_cpheeo.extract import open_clean

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/transcriptions'


def main():
    con = sqlite3.connect(ROOT / 'data/build/cpheeo.sqlite')
    con.row_factory = sqlite3.Row
    manifest = {'schema_version': 1, 'manuals': {}}
    for m in MANUALS:
        path = sources_dir() / m.file
        sha = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
        doc = open_clean(path)
        units = list(con.execute('SELECT id,kind,title,page_start,page_end,table_source FROM units WHERE manual_id=?', (m.id,)))
        images = list(con.execute('SELECT unit_id,seq,pdf_page,bbox FROM images WHERE seq < 100000 AND unit_id LIKE ?', (m.id+':%',)))
        pages = []
        for i, p in enumerate(doc, 1):
            skipped = any(a <= i <= b for a,b in m.skip_pages)
            text = p.get_text()
            refs = sorted(set(re.findall(r'\(\s*\d+[.-]\d+[a-z]?\s*\)', text)))
            # Includes inline formulas, vector equations, uncaptioned/scanned tables:
            # every non-skipped page remains in the human review queue regardless of signals.
            pages.append({'pdf_page': i, 'scope': 'excluded_front_matter' if skipped else 'review',
                          'state': 'pending', 'size_points': list(p.rect),
                          'native_characters': len(text.strip()),
                          'embedded_images': len(p.get_image_info()),
                          'vector_paths': len(p.get_drawings()),
                          'equation_number_candidates': refs,
                          'table_units': [u['id'] for u in units if u['kind']=='table' and u['page_start'] <= i <= u['page_end']],
                          'source_images': [{'unit_id':r['unit_id'],'seq':r['seq'],'bbox':json.loads(r['bbox'])} for r in images if r['pdf_page']==i]})
        entry = {'file':m.file,'sha256':sha,'physical_pages':len(doc),
                 'review_pages':sum(p['scope']=='review' for p in pages),
                 'indexed_tables':sum(u['kind']=='table' for u in units),
                 'image_table_units':sum(u['kind']=='table' and u['table_source']=='image' for u in units)}
        manifest['manuals'][m.id] = entry
        header = json.dumps({'manual_id':m.id,'source_sha256':sha})[:-1]
        (DEST / f'{m.id}-pages.json').write_text(
            header+',"pages":[\n'+',\n'.join(json.dumps(p,separators=(',',':')) for p in pages)+'\n]}\n')
        print(m.id, entry, flush=True)
    (DEST / 'sources.json').write_text(json.dumps(manifest, indent=2)+'\n')

if __name__ == '__main__':
    main()
