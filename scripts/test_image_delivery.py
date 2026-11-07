"""Focused image extraction/storage/MCP regression checks (no source manuals needed)."""
import base64
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import pymupdf

from omakase_cpheeo.corpus import MANUALS, Layout
from omakase_cpheeo.extract import Line, Page
from omakase_cpheeo.index import build
from omakase_cpheeo.server import _with_images
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import Unit, _attach_table, _attach_figure, build_units


class ImageDelivery(unittest.TestCase):
    def test_fallback_page_and_multipage_delivery(self):
        with pymupdf.open() as doc, tempfile.TemporaryDirectory() as tmp:
            for n in range(5):
                pg = doc.new_page()
                pg.insert_text((72, 100), f'Original printed value: {n}.50')
            unit = Unit('SEW-2013-A:T1.1', 'SEW-2013-A', 'table', '1.1',
                        'Example', '1', None, 1, 1, '1 - 1', '1 - 1')
            for n in range(5):
                page = Page(n + 1, f'1 - {n + 1}')
                _attach_table(unit, doc, page, None, Line('Table 1.1: Example', (72, 72, 300, 90), 12, True), set())
            self.assertFalse(unit.table_markdown)
            self.assertFalse(unit.table_cells)
            self.assertEqual(len(unit.images), 5)
            lib = Library(build([unit], (MANUALS[0],), Path(tmp) / 'index.sqlite'))
            try:
                clause = lib.get_clause(unit.id)
                response = _with_images(lib, clause, clause)
                images = [c for c in response.content if c.type == 'image']
                self.assertEqual(len(images), 5)  # no silent four-image cutoff
                for n, block in enumerate(images):
                    self.assertEqual(base64.b64decode(block.data), lib.image(unit.id, n)[1])
                    self.assertEqual(clause['images'][n]['page_label'], f'1 - {n + 1}')
                self.assertNotIn('0.50', lib.fetch(unit.id)['text'])
                self.assertNotIn('0.50', lib.search('Example')['results'][0]['snippet'])
                with self.assertRaises(KeyError):
                    lib.image(unit.id, 5)
            finally:
                lib.con.close()

    def test_uncaptioned_images_follow_their_section(self):
        with pymupdf.open() as doc:
            pg = doc.new_page()
            pg.insert_text((72, 72), '1.1 First section', fontname='hebo')
            pg.insert_text((72, 400), '1.2 Second section', fontname='hebo')
            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 100), False)
            pix.clear_with(150)
            for top in (120, 480):
                pg.insert_image((72, top, 272, top + 100), pixmap=pix)
            manual = replace(MANUALS[0], skip_pages=(), appendix_toc_pages=(), layout=Layout(header_max_y=0, footer_min_y=None))
            units = {u.id: u for u in build_units(manual, doc)}
            self.assertLess(units['SEW-2013-A:1.1'].images[0]['bbox'][1], 400)
            self.assertGreater(units['SEW-2013-A:1.2'].images[0]['bbox'][1], 400)

    def test_vector_figure_keeps_complete_page(self):
        with pymupdf.open() as doc:
            pg = doc.new_page()
            pg.draw_rect((72, 100, 300, 300))
            unit = Unit('SEW-2013-A:F1.1', 'SEW-2013-A', 'figure', '1.1',
                        'Vector drawing', '1', None, 1, 1, None, None)
            _attach_figure(unit, doc, Page(1, None), Line('Figure 1.1', (72, 310, 300, 330), 12, True), set())
            image = unit.images[0]
            self.assertEqual(image['bbox'], list(pg.rect))
            self.assertEqual(image['mime'], 'image/jpeg')
            self.assertTrue(image['data'].startswith(b'\xff\xd8'))


if __name__ == '__main__':
    unittest.main()
