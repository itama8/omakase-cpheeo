"""Versioned, visually checked source transcriptions, independent of the built index.

Pending/unclear records are retained for review but NEVER indexed or served as verified.
Source and rendered-region digests fail closed after a PDF or crop changes. All writes
run inside the caller's transaction; serving remains read-only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pymupdf

from .corpus import manual_by_id, sources_dir
from .extract import open_clean

RECORDS = Path(__file__).resolve().parents[2] / 'data/transcriptions/records'
SCHEMA = '''CREATE TABLE IF NOT EXISTS transcriptions (
 id TEXT PRIMARY KEY, unit_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transcription_images (
 unit_id TEXT, seq INTEGER, PRIMARY KEY (unit_id, seq)
);'''
PASSAGE_BASE = 100000


def region_png(doc, region: dict) -> bytes:
    if not 1 <= region['pdf_page'] <= len(doc):
        raise ValueError('transcription page outside source PDF')
    page = doc[region['pdf_page'] - 1]
    rect = pymupdf.Rect(region['bbox'])
    if region['pdf_page'] < 1 or rect.is_empty or not page.rect.contains(rect):
        raise ValueError('transcription region outside source page')
    return page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=rect, alpha=False).tobytes('png')


def readable(record: dict) -> str:
    lines = [f"Visually verified {record['kind']}: {record['title']}"]
    if record['kind'] == 'table':
        lines.append(record['markdown'])
    else:
        lines += [f"Equation {record['number']}: {record['readable']}",
                  f"LaTeX: {record['latex']}"]
        lines += [f"{s['symbol']}: {s['definition']}" for s in record.get('symbols', [])]
    lines += record.get('notes', [])
    if record.get('applicability'):
        lines.append(record['applicability'])
    return '\n'.join(lines)


def content_digest(record: dict) -> str:
    """Bind the visual recheck to the exact authored content and source regions."""
    content = {k:v for k,v in record.items() if k not in ('state','verification','source_image_refs')}
    return hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def load_records(directory: Path = RECORDS) -> list[dict]:
    records, seen = [], set()
    for path in sorted(directory.glob('*.json')):
        r = json.loads(path.read_text())
        if r['id'] in seen:
            raise ValueError(f"duplicate transcription id: {r['id']}")
        seen.add(r['id'])
        if r['state'] not in ('pending', 'unclear', 'verified'):
            raise ValueError(f"invalid transcription state in {path}")
        if r['schema_version'] != 1 or not r['unit_id'].startswith(r['manual_id']+':'):
            raise ValueError(f'invalid transcription identity in {path}')
        if r['state'] == 'verified':
            if r['kind'] not in ('equation', 'table') or not r['regions']:
                raise ValueError(f"missing transcription kind or source region: {path}")
            checks = r.get('verification', {})
            for step in ('transcription', 'visual_recheck'):
                if not checks.get(step, {}).get('observations'):
                    raise ValueError(f"verified record missing {step}: {path}")
            if checks['transcription']['pass_id'] == checks['visual_recheck']['pass_id']:
                raise ValueError(f"recheck must be a distinct visual pass: {path}")
            if r['kind'] == 'table' and not (r.get('markdown') and r.get('rows')):
                raise ValueError(f"table lacks structured cells: {path}")
            if checks['visual_recheck'].get('content_sha256') != content_digest(r):
                raise ValueError(f'verified content changed after visual recheck: {path}')
            if r['kind']=='table':
                headers, rows = r['headers'], r['rows']
                if any(len(row)!=len(headers) or any(not isinstance(cell,str) for cell in row) for row in rows):
                    raise ValueError(f'invalid table cell grid: {path}')
                expected = '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(row)+' |' for row in rows])
                if expected != r['markdown']:
                    raise ValueError(f'table markdown disagrees with cells: {path}')
            if r['kind'] == 'equation' and not (r.get('latex') and r.get('readable')):
                raise ValueError(f"equation lacks math: {path}")
        records.append(r)
    return records


def apply(con: sqlite3.Connection, directory: Path = RECORDS) -> int:
    """Reapply overlays idempotently; used by both full ingestion and offline refresh."""
    for statement in SCHEMA.split(";"):
        if statement.strip():
            con.execute(statement)
    records = load_records(directory)
    manuals = {r[0] for r in con.execute('SELECT id FROM manuals')}
    records = [r for r in records if r['manual_id'] in manuals and r.get('regions')]
    docs = {}
    try:
        # Validate the ENTIRE batch before mutating the index.
        for r in records:
            mid = r['manual_id']
            if mid not in docs:
                path = sources_dir() / manual_by_id(mid).file
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                docs[mid] = (digest, open_clean(path))
            digest, doc = docs[mid]
            if digest != r['source_sha256']:
                raise ValueError(f"source hash mismatch: {r['id']}")
            for region in r['regions']:
                if hashlib.sha256(region_png(doc, region)).hexdigest() != region['render_sha256']:
                    raise ValueError(f"rendered source region changed: {r['id']}")
            target = r['unit_id'] if r['kind']=='table' else r['parent_id']
            if not con.execute('SELECT 1 FROM units WHERE id=?', (target,)).fetchone():
                raise ValueError(f"missing transcription target: {target}")
        old_equations = [r[0] for r in con.execute("SELECT unit_id FROM transcriptions WHERE kind='equation'")]
        for uid, seq in con.execute('SELECT unit_id,seq FROM transcription_images').fetchall():
            con.execute('DELETE FROM images WHERE unit_id=? AND seq=?', (uid,seq))
        con.execute('DELETE FROM transcription_images')
        con.execute('DELETE FROM passages WHERE seq >= ?', (PASSAGE_BASE,))
        for uid in old_equations:
            con.execute('DELETE FROM units WHERE id=?', (uid,))
            con.execute('DELETE FROM images WHERE unit_id=?', (uid,))
        con.execute('DELETE FROM transcriptions')
        for seq, r in enumerate(records, PASSAGE_BASE):
            body = readable(r) if r['state']=='verified' else f"Unverified source region ({r['state']}); read the original image."
            if r['kind']=='equation':
                parent = con.execute('SELECT chapter,number,ord FROM units WHERE id=?', (r['parent_id'],)).fetchone()
                first = min(r['regions'],key=lambda reg:reg['pdf_page'])
                last = max(r['regions'],key=lambda reg:reg['pdf_page'])
                con.execute('INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                    r['unit_id'], r['manual_id'], 'equation', r['number'], r['title'], parent[0], parent[1],
                    first['pdf_page'], last['pdf_page'], first['page_label'], last['page_label'],
                    '', '', '[]', '', len(r['regions']), 0, '[]', '[]', parent[2]))
            served = dict(r)
            served['source_image_refs'] = []
            for n, region in enumerate(r['regions']):
                # Keep all original image URLs and add exact verified-region crops.
                im_seq = n if r['kind']=='equation' else PASSAGE_BASE + n
                data = region_png(docs[r['manual_id']][1], region)
                pix = pymupdf.Pixmap(data)
                con.execute('INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?)', (
                    r['unit_id'], im_seq, region['pdf_page'], region['page_label'], json.dumps(region['bbox']),
                    pix.width, pix.height, 'image/png', data))
                con.execute('INSERT INTO transcription_images VALUES (?,?)', (r['unit_id'],im_seq))
                served['source_image_refs'].append({'unit_id':r['unit_id'], 'seq':im_seq, **region})
            con.execute('INSERT INTO transcriptions VALUES (?,?,?,?)', (r['id'],r['unit_id'],r['kind'],json.dumps(served,ensure_ascii=False)))
            handle = ('equation eq ' if r['kind']=='equation' else 'table ') + r['number']
            # Preserve each record as a full passage; a row label and its numbers stay together.
            if r['state']=='verified' or r['kind']=='equation':
                con.execute('INSERT INTO passages VALUES (?,?,?,?,?)', (r['unit_id'],seq,handle,r['title'],body))
        con.execute('UPDATE units SET image_count=(SELECT count(*) FROM images WHERE unit_id=units.id)')
        return sum(r['state']=='verified' for r in records)
    finally:
        for _, doc in docs.values():
            doc.close()


def refresh(db: Path, directory: Path = RECORDS) -> int:
    """Build a replacement offline snapshot; never edit a serving database in place."""
    import shutil
    tmp = db.with_suffix('.transcriptions.tmp')
    if tmp.exists():
        raise FileExistsError(f'remove stale refresh snapshot after inspection: {tmp}')
    shutil.copyfile(db, tmp)
    con = sqlite3.connect(tmp)
    try:
        count = apply(con, directory)
        con.commit()
        con.execute("INSERT INTO passages(passages) VALUES ('optimize')")
        con.commit()
        con.close()
        tmp.replace(db)
        return count
    except BaseException:
        con.close()
        tmp.unlink(missing_ok=True)
        raise
