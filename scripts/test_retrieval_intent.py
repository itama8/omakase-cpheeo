"""Source-independent retrieval behavior with arbitrary, non-corpus identifiers."""
from pathlib import Path
import tempfile
import unittest

from omakase_cpheeo.corpus import MANUALS
from omakase_cpheeo.index import build
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import Unit


class RetrievalIntent(unittest.TestCase):
    def library(self, units):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        lib = Library(build(units, (MANUALS[0],), Path(tmp.name)/'index.sqlite'))
        self.addCleanup(lib.con.close)
        return lib

    def unit(self, number, title, text, parent=None):
        return Unit('SEW-2013-A:'+number,'SEW-2013-A','section',number,title,'8',parent,1,1,'1','1',text=text)

    def test_exact_title_ignores_punctuation_and_possessive(self):
        lib = self.library([
            self.unit('8.91',"Manning’s Roughness",'General source guidance for conduits.'),
            self.unit('8.92','Manning roughness Manning roughness Manning roughness', 'Manning roughness values.')])
        self.assertEqual(lib.search("Manning's roughness")['results'][0]['id'],'SEW-2013-A:8.91')
        # Explicit reference still wins over the title rule.
        self.assertEqual(lib.search('Section 8.92 Manning roughness')['results'][0]['id'],'SEW-2013-A:8.92')

    def test_design_query_demotes_example_through_owning_heading(self):
        lib = self.library([
            self.unit('8.71','Illustrative Examples','Worked calculations.'),
            self.unit('8.71.1','Pump design','Pump design criteria.', '8.71'),
            self.unit('8.72','Pump design','Pump design criteria.')])
        # Without design intent equal text keeps source order; with intent the
        # owning example heading must not beat the equally relevant criterion.
        self.assertEqual(lib.search('pump design criteria')['results'][0]['id'],'SEW-2013-A:8.72')
        self.assertEqual(lib.search('example pump design criteria')['results'][0]['id'],'SEW-2013-A:8.71.1')
        self.assertEqual(lib.search('Section 8.71.1 pump design criteria')['results'][0]['id'],'SEW-2013-A:8.71.1')


if __name__=='__main__':unittest.main()
