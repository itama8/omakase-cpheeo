"""Verify every Part A appendix and its full-page images against the native contents."""
import re
import sys

from omakase_cpheeo.corpus import manual_by_id, sources_dir
from omakase_cpheeo.extract import open_clean, read_page
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import appendix_catalogue

lib = Library(sys.argv[1] if len(sys.argv) > 1 else None)
manual = manual_by_id('SEW-2013-A')
with open_clean(sources_dir() / manual.file) as doc:
    catalogue = appendix_catalogue(manual, doc)
    assert len(catalogue) == 51, '2013 Part A contents list 51 appendices/sheets'
    labels = {}
    for n in range(max(manual.appendix_toc_pages), len(doc)):
        page = read_page(doc[n], manual.layout)
        if page.label:
            labels[page.label] = page.number
    toc = '\n'.join(doc[n - 1].get_text() for n in manual.appendix_toc_pages)
    reference = re.search(r'References\s*\.{2,}\s*A\s*-\s*(\d+)', toc, re.I)
    assert reference
    reference_page = labels['A - ' + reference.group(1)]
    starts = sorted((labels[label], number, title) for label, (number, title) in catalogue.items())
    covered = set()
    for i, (start, number, title) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else reference_page - 1
        rows = lib.con.execute("SELECT * FROM units WHERE manual_id=? AND kind='appendix' AND replace(number,'-','.')=?", (manual.id, number)).fetchall()
        assert len(rows) == 1, (number, len(rows))
        row = rows[0]
        assert row['title'] == title, (number, row['title'], title)
        assert (row['page_start'], row['page_end']) == (start, end), (number, row['page_start'], row['page_end'], start, end)
        images = lib.image_refs(row['id'])
        expected = set(range(start, end + 1))
        assert {r['pdf_page'] for r in images} == expected, (number, expected)
        for image in images:
            rect = [round(v, 1) for v in doc[image['pdf_page'] - 1].rect]
            assert image['bbox'] == rect, (number, image)
            assert image['page_label'] and image['width'] > 0 and image['height'] > 0
        covered.update(expected)
    assert covered == set(range(starts[0][0], reference_page))
    print(f'PASS: {len(starts)} source-listed appendices/sheets; {len(covered)} printed pages; complete titles, boundaries and full-page images')
