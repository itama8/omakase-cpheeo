"""Paraphrase groups are scored on their worst-ranked phrasing."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from omakase_cpheeo.corpus import MANUALS
from omakase_cpheeo.evaluate import run_groups, score_groups
from omakase_cpheeo.index import build
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import Unit


class ParaphraseGroups(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        unit = lambda n, title, text: Unit('SEW-2013-A:'+n, 'SEW-2013-A', 'section', n, title, '8', None, 1, 1, '1', '1', text=text)
        self.lib = Library(build([unit('8.1', 'Grit Removal', 'Grit chambers follow the pumps in deep sewers.'),
                                  unit('8.2', 'Screens', 'Bar screens ahead of pumps.')],
                                 (MANUALS[0],), Path(tmp.name)/'index.sqlite'))
        self.addCleanup(self.lib.con.close)

    def test_worst_phrasing_decides_the_group(self):
        groups = [{'id': 'G1', 'target': 'grit', 'expect': ['SEW-2013-A:8.1'],
                   'phrasings': ['grit removal', {'q': 'bar screens ahead of pumps', 'style': 'gap'}, 'velocity of flow']}]
        ranks = [r['rank'] for r in score_groups(self.lib, groups)[0]['scored']]
        self.assertEqual(ranks[0], 1)
        self.assertGreater(ranks[1], 1)   # the screens section ranks first
        self.assertIsNone(ranks[2])        # nothing matches at all
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(run_groups(self.lib, groups, k=5), 1)
        self.assertIn('FAIL   G1  worst >25  hit@1 1/3  hit@5 2/3', out.getvalue())
        self.assertIn('0/1 groups', out.getvalue())


if __name__ == '__main__':
    unittest.main()
