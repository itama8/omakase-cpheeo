"""Source-independent contracts: immutable evidence, rejection, re-ingestion and delivery."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pymupdf

from omakase_cpheeo.corpus import MANUALS
from omakase_cpheeo.extract import open_clean
from omakase_cpheeo.index import build
from omakase_cpheeo.server import _clause_html, _with_images
from omakase_cpheeo.service import Library
from omakase_cpheeo.structure import Unit
from omakase_cpheeo.transcriptions import content_digest, load_records, refresh, region_png


class Transcriptions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.records = self.root / 'records'
        self.records.mkdir()
        pdf = self.root / MANUALS[0].file
        with pymupdf.open() as doc:
            for text in ('Source: temperature 30; solubility 7.5', 'Continuation: 100 (boiling); 0.0'):
                doc.new_page().insert_text((72,100),text)
            doc.save(pdf)
        self.source_patch = patch.dict(os.environ, OMAKASE_CPHEEO_SOURCES=str(self.root))
        self.source_patch.start()
        self.addCleanup(self.source_patch.stop)
        self.base = [Unit('SEW-2013-A:T2.1','SEW-2013-A','table','2.1','Source table','2','2.5',1,1,'2 - 1','2 - 1',table_source='image'),
                     Unit('SEW-2013-A:2.5','SEW-2013-A','section','2.5','Aeration','2','2',1,2,'2 - 1','2 - 2')]
        with open_clean(pdf) as doc:
            self.regions = []
            for n in (1,2):
                reg = {'pdf_page':n,'page_label':f'2 - {n}','bbox':[50,70,500,130]}
                reg['render_sha256'] = hashlib.sha256(region_png(doc,reg)).hexdigest()
                self.regions.append(reg)
        self.template = {'schema_version':1,'manual_id':'SEW-2013-A','source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
                         'state':'verified','regions':self.regions,'notes':[],
                         'verification':{'transcription':{'pass_id':'fixture-first','observations':'fixture'},'visual_recheck':{'pass_id':'fixture-second','observations':'fixture'}}}
        self.table = {**self.template,'id':'SEW-2013-A:T2.1','unit_id':'SEW-2013-A:T2.1','kind':'table','number':'2.1','title':'Oxygen solubility',
                      'headers':['Temperature','Oxygen solubility (mg/l)'],'rows':[['30','7.5'],['100 (boiling)','0.0']],
                      'markdown':'| Temperature | Oxygen solubility (mg/l) |\n| --- | --- |\n| 30 | 7.5 |\n| 100 (boiling) | 0.0 |'}
        self.eq = {**self.template,'id':'SEW-2013-A:E5.30','unit_id':'SEW-2013-A:E5.30','kind':'equation','number':'5.30',
                   'title':'Oxygen transfer capacity','parent_id':'SEW-2013-A:2.5',
                   'latex':r'N=\frac{N_s(C_s-C_L)1.024^{T-20}\alpha}{9.17}',
                   'readable':'N = N_s (C_s - C_L) 1.024^(T-20) alpha / 9.17'}
        self.write(self.table)
        self.write(self.eq)
        self.db = self.root / 'index.sqlite'

    def write(self,r):
        # Deep copy prevents fixtures from accidentally sharing a verification dictionary.
        r = json.loads(json.dumps(r))
        r['verification']['visual_recheck']['content_sha256'] = content_digest(r)
        (self.records / (r['id'].replace(':','--')+'.json')).write_text(json.dumps(r))

    def rebuild(self):
        build(self.base,(MANUALS[0],),self.db,transcription_records=self.records)

    def test_ingestion_refresh_and_removal_preserve_source_and_images(self):
        self.rebuild()
        lib = Library(self.db)
        clause = lib.get_clause(self.table['unit_id'])
        self.assertEqual(clause['verified_transcriptions'][0]['rows'][1],['100 (boiling)','0.0'])
        self.assertIn('2 - 1 to 2 - 2',clause['citation'])
        self.assertEqual(clause['page_label_end'],'2 - 2')
        self.assertEqual(clause['pdf_page_end'],2)
        self.assertEqual(len(clause['images']),2)
        first_image = lib.image(self.table['unit_id'],100000)[1]
        self.assertIn('7.5',lib.fetch(self.table['unit_id'])['text'])
        self.assertEqual(lib.search('Equation 5.30')['results'][0]['id'],self.eq['id'])
        parent = lib.get_clause('SEW-2013-A:2.5')
        self.assertEqual(parent['equations'][0]['id'],self.eq['id'])
        self.assertIn('9.17',lib.fetch(parent['id'])['text'])
        self.assertIn('9.17',_clause_html(parent))
        response = _with_images(lib,parent,parent)
        self.assertEqual(len([b for b in response.content if b.type=='image']),4)  # child table + equation
        self.assertEqual(clause['text'],'')  # underlying native text remains unchanged
        lib.con.close()
        refresh(self.db,self.records)
        lib = Library(self.db)
        self.assertEqual(lib.image(self.table['unit_id'],100000)[1],first_image)
        self.assertEqual(len(lib.get_clause(self.table['unit_id'])['images']),2)
        lib.con.close()
        self.rebuild()  # full re-ingestion preserves versioned overrides too
        lib = Library(self.db)
        self.assertIn('9.17',lib.get_clause(self.eq['id'])['verified_text'])
        lib.con.close()
        for p in self.records.glob('*.json'):p.unlink()
        refresh(self.db,self.records)
        lib = Library(self.db)
        self.assertNotIn('verified_text',lib.get_clause(self.table['id']))
        self.assertEqual(lib.get_clause(self.table['id']).get('images',[]),[])
        with self.assertRaises(KeyError):lib.get_clause(self.eq['id'])
        lib.con.close()

    def test_pending_unclear_and_changed_evidence_fail_closed(self):
        self.rebuild()
        original_digest = hashlib.sha256(self.db.read_bytes()).hexdigest()
        r = json.loads(json.dumps(self.table))
        r['source_sha256'] = '0'*64
        self.write(r)
        with self.assertRaisesRegex(ValueError,'source hash mismatch'):refresh(self.db,self.records)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),original_digest)
        r = json.loads(json.dumps(self.table))
        r['regions'][0]['render_sha256'] = '0'*64
        self.write(r)
        with self.assertRaisesRegex(ValueError,'rendered source region changed'):refresh(self.db,self.records)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),original_digest)
        for state in ('pending','unclear'):
            r = {**self.table,'state':state}
            self.write(r)
            refresh(self.db,self.records)
            lib = Library(self.db)
            self.assertNotIn('verified_text',lib.get_clause(self.table['id']))
            self.assertFalse(any(h['id']==self.table['id'] for h in lib.search('solubility')['results']))
            lib.con.close()

    def test_unclear_equation_keeps_image_without_asserting_math(self):
        r = {**self.eq,'state':'unclear','notes':['Powers cannot be determined.']}
        self.write(r)
        self.rebuild()
        lib = Library(self.db)
        c = lib.get_clause(r['id'])
        self.assertEqual(c['transcription_status'],'unclear')
        self.assertNotIn('verified_text',c)
        self.assertTrue(c['images'])
        self.assertNotIn('9.17',lib.fetch(r['id'])['text'])
        self.assertIn('Unverified',lib.fetch('SEW-2013-A:2.5')['text'])
        self.assertIn('Unverified',_clause_html(c))
        lib.con.close()

    def test_content_cannot_change_after_recheck(self):
        p = self.records / 'SEW-2013-A--T2.1.json'
        r = json.loads(p.read_text())
        r['rows'][0][1] = '75'  # a lost decimal must invalidate verification
        p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,'content changed after visual recheck'):load_records(self.records)

    def test_discovered_table_survives_rebuild_refresh_and_removal(self):
        table = {**self.table, 'id':'SEW-2013-A:Tp1-1', 'unit_id':'SEW-2013-A:Tp1-1',
                 'number':'p1-1', 'create_unit':True, 'parent_id':'SEW-2013-A:2.5',
                 'notes':['Service locator, not a printed table number.']}
        self.write(table)
        self.rebuild()
        for operation in (lambda:None, lambda:refresh(self.db,self.records), self.rebuild):
            operation()
            lib = Library(self.db)
            c = lib.get_clause(table['id'])
            self.assertEqual(c['verified_transcriptions'][0]['rows'],table['rows'])
            self.assertEqual(c['parent'],table['parent_id'])
            self.assertIn(table['id'],[t['id'] for t in lib.get_clause(table['parent_id'])['tables']])
            self.assertIn('7.5',lib.fetch(table['id'])['text'])
            self.assertTrue(lib.image(table['id'],100000)[1])
            lib.con.close()
        self.write({**table,'state':'pending'})
        refresh(self.db,self.records)
        lib = Library(self.db)
        self.assertNotIn('verified_text',lib.get_clause(table['id']))
        lib.con.close()
        (self.records/'SEW-2013-A--Tp1-1.json').unlink()
        refresh(self.db,self.records)
        lib = Library(self.db)
        with self.assertRaises(KeyError):lib.get_clause(table['id'])
        self.assertEqual(lib.get_clause(self.table['id'])['verified_transcriptions'][0]['rows'],self.table['rows'])
        lib.con.close()

    def test_discovered_table_cannot_replace_original_or_use_foreign_parent(self):
        self.rebuild()
        original = hashlib.sha256(self.db.read_bytes()).hexdigest()
        self.write({**self.table,'create_unit':True,'parent_id':'SEW-2013-A:2.5'})
        with self.assertRaisesRegex(ValueError,'replace an original unit'):refresh(self.db,self.records)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),original)
        self.write({**self.table,'create_unit':True,'parent_id':'WS-2024-A:2.5'})
        with self.assertRaisesRegex(ValueError,'another manual'):refresh(self.db,self.records)
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(),original)


if __name__=='__main__':unittest.main()
