"""Check appendix handles, multipart sheets and source-page boundaries without the manuals."""
from dataclasses import replace
import unittest
import tempfile
from pathlib import Path

import pymupdf

from omakase_cpheeo.corpus import MANUALS
from omakase_cpheeo.extract import Line, read_page
from omakase_cpheeo.index import build, explicit_refs
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import _heading, appendix_catalogue, build_units


class Appendices(unittest.TestCase):
    def test_heading_variants(self):
        for text, number, title in [
            ('APPENDIX A.1.1 The Act', 'A1.1', 'The Act'),
            ('APPENDIX.AA-List of Indian Standards', 'AA', 'List of Indian Standards'),
            ('APPENDIX A 3.4 A', 'A3.4A', ''),
            ('APPENDIX A 3.4 B', 'A3.4B', ''),
            ('Appendix A 5-9', 'A5-9', ''),
        ]:
            with self.subTest(text=text):
                self.assertEqual(_heading(Line(text, (200, 73, 500, 90), 11, True)), ('appendix', number, title))

    def test_native_contents_inline_and_wrapped_titles(self):
        manual = replace(MANUALS[0], appendix_toc_pages=(1,))
        with pymupdf.open() as doc:
            pg = doc.new_page()
            pg.insert_text((72, 100), 'A 3.3\nMS Excel for Manning formula..A-58\nA 3.4 B MS Excel example........A-60')
            entries = appendix_catalogue(manual, doc)
            self.assertEqual(entries['A - 58'], ('A3.3', 'MS Excel for Manning formula'))
            self.assertEqual(entries['A - 60'], ('A3.4B', 'MS Excel example'))

    def test_separate_sheets_preserve_legacy_group_and_images(self):
        manual = replace(MANUALS[0], skip_pages=(), appendix_toc_pages=())
        with pymupdf.open() as doc:
            for suffix in ('A', 'B'):
                pg = doc.new_page()
                pg.insert_text((180, 80), f'APPENDIX A 3.4 {suffix}', fontname='hebo')
                pg.insert_text((72, 100), f'Computations for sheet {suffix}', fontname='hebo')
                pg.insert_text((72, 140), 'Native content for this sheet ' * 5)
            units = {u.id: u for u in build_units(manual, doc)}
            self.assertEqual(units['SEW-2013-A:A3.4A'].page_end, 1)
            self.assertEqual(units['SEW-2013-A:A3.4B'].page_start, 2)
            self.assertEqual([i['pdf_page'] for i in units['SEW-2013-A:A3.4A'].images], [1])
            self.assertEqual([i['pdf_page'] for i in units['SEW-2013-A:A3.4'].images], [1, 2])
            self.assertIn('sheet B', units['SEW-2013-A:A3.4'].text)
            self.assertEqual(units['SEW-2013-A:A3.4A'].title, 'Computations for sheet A')
            with tempfile.TemporaryDirectory() as tmp:
                lib = Library(build(list(units.values()), (manual,), Path(tmp) / 'index.sqlite'))
                try:
                    ids = [r['id'] for r in lib.search('Computations')['results']]
                    self.assertNotIn('SEW-2013-A:A3.4', ids)
                    self.assertIn('SEW-2013-A:A3.4A', ids)
                    self.assertEqual(lib.search('Appendix A 3.4')['results'][0]['id'], 'SEW-2013-A:A3.4')
                finally:
                    lib.con.close()

    def test_scanned_heading_and_lettered_table_are_citable(self):
        manual = replace(MANUALS[0], skip_pages=((1, 1),), appendix_toc_pages=(1,))
        with pymupdf.open() as doc:
            toc = doc.new_page()
            toc.insert_text((72, 100), 'A 7.1 Micro nutrients...............A-144')
            pg = doc.new_page()
            pg.insert_text((72, 800), 'A - 144')
            pg.insert_text((72, 130), 'Table A 7.1- 1 Nutrients', fontname='hebo')
            pg.insert_text((72, 170), 'Original page content ' * 8)
            units = {u.id: u for u in build_units(manual, doc)}
            self.assertIn('SEW-2013-A:TA7.1-1', units)
            self.assertEqual(units['SEW-2013-A:TA7.1-1'].parent, 'A7.1')
            self.assertEqual(len(units['SEW-2013-A:A7.1'].images), 1)

    def test_printed_appendix_references(self):
        self.assertEqual(explicit_refs('Appendix A 3.2 B'), [('appendix', 'A3.2B')])
        self.assertEqual(explicit_refs('Table A 7.3- 1'), [('table', 'A7.3-1')])
        self.assertEqual(explicit_refs('Figure A3.2A-1'), [('figure', 'A3.2A-1')])
        self.assertEqual(explicit_refs('Table 3.2 a peak factor'), [('table', '3.2')])

    def test_old_dotted_handle_keeps_working(self):
        manual = replace(MANUALS[0], skip_pages=(), appendix_toc_pages=())
        with pymupdf.open() as doc, tempfile.TemporaryDirectory() as tmp:
            pg = doc.new_page()
            pg.insert_text((180, 80), 'APPENDIX A.1.1', fontname='hebo')
            pg.insert_text((72, 100), 'The Act', fontname='hebo')
            pg.insert_text((72, 140), 'Original content ' * 12)
            lib = Library(build(build_units(manual, doc), (manual,), Path(tmp) / 'index.sqlite'))
            try:
                self.assertEqual(lib.get_clause('SEW-2013-A:A.1.1')['id'], 'SEW-2013-A:A1.1')
                self.assertEqual(lib.image('SEW-2013-A:A.1.1', 0), lib.image('SEW-2013-A:A1.1', 0))
            finally:
                lib.con.close()

    def test_rotated_footer_label(self):
        with pymupdf.open() as doc:
            pg = doc.new_page()
            pg.insert_text((550, 430), 'A - 144', rotate=90)
            self.assertEqual(read_page(pg).label, 'A - 144')


if __name__ == '__main__':
    unittest.main()
