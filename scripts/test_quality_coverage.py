"""Source-independent checks: coverage notices, text-quality signals and structured errors."""
import asyncio
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from omakase_cpheeo.corpus import MANUALS
from omakase_cpheeo.index import build
from omakase_cpheeo.quality import TextDefects, annotate, enumeration_gaps
from omakase_cpheeo.service import SEARCH_KINDS, InvalidArgument, Library, UnknownId
from omakase_cpheeo.structure import Unit


def unit(number, title, text, parent=None):
    return Unit('SEW-2013-A:'+number, 'SEW-2013-A', 'section', number, title, '4', parent, 1, 1, '1', '1', text=text)


class Fixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.lib = Library(build([
            unit('4.7', 'Pumping Head', 'Overview of pumping head.'),
            unit('4.7.2', 'Computation of the Total Head', 'Firstly, the static head.\nThirdly, the pressure head. The velocity head is 2/2g.', '4.7'),
            unit('4.8', 'Storm Runoff', 'Storm runoff enters combined sewers. Design return period for sewers.'),
        ], (MANUALS[0],), self.dir/'index.sqlite'))
        self.addCleanup(self.lib.con.close)
        defects = self.dir/'defects.json'
        defects.write_text(json.dumps({'schema_version': 1, 'defects': [
            {'unit_id': 'SEW-2013-A:4.7.2', 'extracted': 'velocity head is 2/2g', 'reading': 'velocity head is V²/2g',
             'verified_id': 'SEW-2013-A:Ep1', 'note': 'superscript lost'}]}))
        self.lib.__dict__['defects'] = TextDefects(defects)


class Coverage(Fixture):
    def status(self, query, **kw):
        return self.lib.search(query, **kw)['coverage']['status']

    def test_named_unindexed_manual_is_reported_even_with_results(self):
        r = self.lib.search('design return period in the CPHEEO Storm Water Drainage Manual')
        self.assertTrue(r['results'])  # sewerage results are kept ...
        self.assertEqual(r['coverage']['status'], 'requested_manual_not_indexed')  # ... but flagged
        self.assertEqual(r['coverage']['not_indexed'][0]['domain'], 'stormwater')
        self.assertEqual(self.status('stormwater manual return period'), 'requested_manual_not_indexed')

    def test_filters_for_unindexed_scope_say_so(self):
        self.assertEqual(self.status('return period', domain='stormwater'), 'domain_not_indexed')
        self.assertEqual(self.status('return period', domain='drainage'), 'unknown_domain')
        self.assertEqual(self.status('return period', manual_id='SWD-2019-A'), 'manual_not_indexed')
        self.assertEqual(self.status('return period', manual_id='NOPE'), 'unknown_manual')

    def test_topic_no_match_and_ok(self):
        self.assertEqual(self.status('landfill liner requirements'), 'topic_may_be_outside_corpus')
        self.assertEqual(self.status('zzzz qqqq'), 'no_match')
        self.assertEqual(self.status('storm runoff combined sewers'), 'ok')

    def test_list_manuals_names_unindexed(self):
        ids = {m['id'] for m in self.lib.list_manuals()['not_indexed']}
        self.assertTrue({'SWD-2019', 'MSW-2016'} <= ids)


class TextQuality(Fixture):
    def test_gap_detection(self):
        self.assertEqual([g.missing for g in enumeration_gaps('Firstly, a.\nThirdly, b.')], [('Secondly',)])
        self.assertEqual([g.missing for g in enumeration_gaps('(a) one\n(b) two (d) four')], [('c',)])
        self.assertEqual(enumeration_gaps('(c) continues\n(d) a list begun earlier'), [])
        self.assertEqual(enumeration_gaps('Firstly, a. Secondly, b.'), [])
        self.assertEqual(enumeration_gaps('only (a) one item'), [])

    def test_clause_marks_defects_and_omissions_without_editing_text(self):
        c = self.lib.get_clause('SEW-2013-A:4.7.2')
        self.assertIn('2/2g.', c['text'])  # raw text kept for traceability
        self.assertTrue(c['text_quality']['known_defects'][0]['located'])
        self.assertEqual(c['text_quality']['possible_omissions'][0]['missing'], ['Secondly'])
        self.assertIn('[extraction defect: the printed page reads "velocity head is V²/2g"; see SEW-2013-A:Ep1]', c['reading_text'])
        self.assertIn('[possible omission: Secondly missing', c['reading_text'])
        self.assertLess(c['reading_text'].index('possible omission'), c['reading_text'].index('Thirdly'))
        self.assertIn('evidence_precedence', c)
        self.assertNotIn('text_quality', self.lib.get_clause('SEW-2013-A:4.7'))

    def test_fetch_labels_layers_and_search_flags_quality(self):
        text = self.lib.fetch('SEW-2013-A:4.7.2')['text']
        self.assertIn('[EXTRACTED TEXT: PDF text layer, not visually verified; known defects', text)
        self.assertIn('[extraction defect', text)
        hit = next(r for r in self.lib.search('computation total head')['results'] if r['id'] == 'SEW-2013-A:4.7.2')
        self.assertEqual(hit['quality_flags'], ['known_extraction_defects', 'possible_omissions'])

    def test_unlocated_defect_is_listed_but_not_inserted(self):
        self.assertEqual(annotate('abc', [{'extracted': 'zz', 'reading': 'y', 'located': False}], []), 'abc')


class Errors(Fixture):
    def test_unknown_ids_suggest_recovery(self):
        with self.assertRaises(UnknownId) as e:
            self.lib.get_clause('SEW-2013-A:4.7.9')
        self.assertEqual(e.exception.code, 'unknown_id')
        self.assertIn('SEW-2013-A:4.7.2', e.exception.suggestions)
        self.assertEqual(str(e.exception), "no unit 'SEW-2013-A:4.7.9' in SEW-2013-A")  # no KeyError quoting
        with self.assertRaises(UnknownId) as e:
            self.lib.get_clause('SWD-2019-A:1.1')
        self.assertEqual(e.exception.code, 'unknown_manual')
        with self.assertRaises(UnknownId) as e:
            self.lib.get_clause('4.7.2')
        self.assertEqual(e.exception.suggestions, ['SEW-2013-A:4.7.2'])
        with self.assertRaises(KeyError):  # REST handlers still map it to 404
            self.lib.get_toc('NOPE')

    def test_invalid_kind(self):
        with self.assertRaises(InvalidArgument) as e:
            self.lib.search('head', kind='equations')
        self.assertEqual(e.exception.suggestions, list(SEARCH_KINDS))
        self.assertTrue(self.lib.search('head', kind='section')['results'])

    def test_mcp_tools_return_structured_errors_and_document_kinds(self):
        from omakase_cpheeo import server
        with mock.patch.object(server, 'Library', return_value=self.lib):
            mcp = server.build_server()
        tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
        for kind in SEARCH_KINDS:
            self.assertIn(kind, tools['search'].description)
        for name, args in [('get_clause', {'id': 'SEW-2013-A:9.99'}), ('fetch', {'id': 'SEW-2013-A:9.99'}),
                           ('search', {'query': 'x', 'kind': 'bogus'}), ('get_toc', {'manual': 'NOPE'})]:
            res = asyncio.run(mcp.call_tool(name, args))
            self.assertTrue(res.is_error, name)
            self.assertIn(res.structured_content['error']['code'], {'unknown_id', 'invalid_kind', 'unknown_manual'}, name)
        ok = asyncio.run(mcp.call_tool('search', {'query': 'storm runoff'}))
        self.assertFalse(ok.is_error)
        self.assertEqual(ok.structured_content['coverage']['status'], 'ok')


if __name__ == '__main__':
    unittest.main()
