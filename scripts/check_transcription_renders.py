"""Verify pinned crop bytes after full-page and repeated rendering in one session."""
import hashlib

import pymupdf

from omakase_cpheeo.corpus import manual_by_id, sources_dir
from omakase_cpheeo.extract import open_clean
from omakase_cpheeo.transcriptions import load_records, region_png

records = load_records()
count = 0
for mid in sorted({r['manual_id'] for r in records}):
    with open_clean(sources_dir()/manual_by_id(mid).file) as doc:
        for r in records:
            if r['manual_id'] != mid:
                continue
            for reg in r['regions']:
                # Keep the Page alive: that reproduced the order-dependent
                # mismatch before region_png reloaded the cached page object.
                page = doc[reg['pdf_page']-1]
                page.get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False)
                for _ in range(2):
                    actual = hashlib.sha256(region_png(doc,reg)).hexdigest()
                    assert actual == reg['render_sha256'], (r['id'],reg['pdf_page'],actual)
                count += 1
print(f'PASS: {count} pinned regions stable after full-page and repeated renders')
