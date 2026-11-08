"""Check retrieved content, exact rows and provenance, not just expected handles.

Latency is local in-process search+fetch, with warm repeats; no network/provider claims.
"""
import json
from pathlib import Path
import statistics
import sys
import time

import yaml

from omakase_cpheeo.service import Library

lib=Library(sys.argv[1] if len(sys.argv)>1 else None)
questions=yaml.safe_load((Path(__file__).resolve().parents[1]/'eval/verified-transcriptions.yaml').read_text())['questions']
failed=[];latencies=[];ranks=[]
for q in questions:
    found=lib.search(q['question'],limit=5)['results']
    rank=next((i+1 for i,r in enumerate(found) if r['id'] in q['expect']),None)
    errors=[]
    if rank is None:errors.append('not retrieved in top five')
    for uid in q['expect']:
        clause=lib.get_clause(uid);doc=lib.fetch(uid)
        if clause.get('transcription_status')!='verified':errors.append('missing verified status')
        records=clause.get('verified_transcriptions',[])
        if not records or not clause.get('images'):errors.append('missing evidence')
        for t in records:
            for region in t['source_image_refs']:
                mime,data=lib.image(uid,region['seq'])
                if not data.startswith(b'\x89PNG') or mime!='image/png':errors.append('missing source-region image')
        for text in q.get('contains',[]):
            if text not in doc['text']:errors.append(f'missing content {text!r}')
        if 'row' in q and not any(q['row'] in t.get('rows',[]) for t in records):errors.append('wrong numerical row')
        if 'via Omakase CPHEEO' not in doc['text']:errors.append('missing attribution')
    for _ in range(5):
        start=time.perf_counter();lib.search(q['question'],limit=5);lib.fetch(q['expect'][0]);latencies.append((time.perf_counter()-start)*1000)
    if errors:failed.append({'id':q['id'],'errors':errors})
    ranks.append(rank)
    print((('FAIL' if errors else 'PASS')+f" {q['id']} rank={rank} "+'; '.join(errors)).rstrip())
result={'questions':len(questions),'content_checks_passed':len(questions)-len(failed),'top1':ranks.count(1),'top5':sum(r is not None for r in ranks),
        'mrr':sum(1/r if r else 0 for r in ranks)/len(ranks),'local_warm_search_fetch_ms':{'samples':len(latencies),'median':statistics.median(latencies),'p95':sorted(latencies)[int(.95*(len(latencies)-1))]},
        'limitations':'Source-open regression set. Same-assistant visual recheck, not independent accuracy proof. In-process warm SQLite timings exclude network, rendering, model and end-to-end retrieval time.','failures':failed}
print(json.dumps(result,indent=2))
lib.con.close()
sys.exit(bool(failed))
