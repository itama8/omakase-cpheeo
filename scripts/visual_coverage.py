"""Reproducible counts; detection, page review and verified transcription are separate."""
import json
from collections import Counter
from pathlib import Path

from omakase_cpheeo.transcriptions import RECORDS, load_records

ROOT = RECORDS.parent

def report():
    sources = json.loads((ROOT/'sources.json').read_text())['manuals']
    reviews = json.loads((ROOT/'page-reviews.json').read_text())['manuals']
    tables = json.loads((ROOT/'table-inventory.json').read_text())['tables']
    records = load_records()
    verified = {r['unit_id']:r for r in records if r['state']=='verified'}
    result = {'scope_complete':False,'equation_total':'unknown until every review-scope page is inspected', 'manuals':{}}
    for mid,source in sources.items():
        ledger=json.loads((ROOT/f'{mid}-pages.json').read_text())
        assert ledger['source_sha256']==source['sha256']
        assert [p['pdf_page'] for p in ledger['pages']]==list(range(1,source['physical_pages']+1))
        expected={p['pdf_page'] for p in ledger['pages'] if p['scope']=='review'}
        review=reviews[mid]
        done=set(review['reviewed_pages']); partial={int(p) for p in review['partial_pages']}
        assert done <= expected and partial <= expected and not done & partial
        mine=[t for t in tables if t['manual_id']==mid]
        image_tables=[t for t in mine if t['table_source']=='image']
        v=Counter(r['kind'] for r in verified.values() if r['manual_id']==mid)
        for r in verified.values():
            if r['manual_id']==mid:
                assert r['source_sha256']==source['sha256']
                assert all(reg['pdf_page'] in done|partial for reg in r['regions']),r['id']
        result['manuals'][mid]={
            'physical_pages':source['physical_pages'],'review_scope_pages':len(expected),
            'pages_reviewed':len(done),'pages_partially_reviewed':len(partial),
            'pages_remaining_including_partial':len(expected-done),
            'indexed_tables':len(mine),'baseline_image_table_units':len(image_tables),
            'discovered_table_units_verified':sum(r['manual_id']==mid and r['kind']=='table' and r.get('create_unit') is True for r in verified.values()),
            'baseline_image_table_units_verified':sum(t['id'] in verified for t in image_tables),
            'baseline_image_table_units_pending':sum(t['id'] not in verified for t in image_tables),
            'native_table_units_without_visual_transcription':sum(t['table_source']=='text' and t['id'] not in verified for t in mine),
            'verified_tables':v['table'],'verified_equations':v['equation']}
    return result

if __name__=='__main__':print(json.dumps(report(),indent=2))
