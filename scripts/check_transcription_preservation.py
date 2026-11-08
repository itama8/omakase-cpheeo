"""Compare an overlay snapshot with its unchanged baseline, including every image byte."""
import sqlite3
import sys
from pathlib import Path

if len(sys.argv)!=3:
    raise SystemExit('usage: check_transcription_preservation.py BASELINE.sqlite CANDIDATE.sqlite')
a,b=[sqlite3.connect(f'file:{Path(p).resolve()}?mode=ro',uri=True) for p in sys.argv[1:]]
a.row_factory=b.row_factory=sqlite3.Row
assert list(a.execute('SELECT * FROM manuals ORDER BY id'))==list(b.execute('SELECT * FROM manuals ORDER BY id'))
units=images=passages=0
for row in a.execute('SELECT * FROM units ORDER BY id'):
    new=b.execute('SELECT * FROM units WHERE id=?',(row['id'],)).fetchone()
    assert new is not None,row['id']
    for col in row.keys():
        if col!='image_count':assert row[col]==new[col],(row['id'],col)
    units+=1
for row in a.execute('SELECT * FROM images ORDER BY unit_id,seq'):
    new=b.execute('SELECT * FROM images WHERE unit_id=? AND seq=?',(row['unit_id'],row['seq'])).fetchone()
    assert new is not None and tuple(row)==tuple(new),(row['unit_id'],row['seq'])
    images+=1
for row in a.execute('SELECT * FROM passages WHERE seq<100000 ORDER BY unit_id,seq'):
    new=b.execute('SELECT * FROM passages WHERE unit_id=? AND seq=?',(row['unit_id'],row['seq'])).fetchone()
    assert new is not None and tuple(row)==tuple(new),(row['unit_id'],row['seq'])
    passages+=1
print(f'PASS: all {units} original units (except derived image counts), {images} complete source images and {passages} original passages are unchanged')
a.close();b.close()
