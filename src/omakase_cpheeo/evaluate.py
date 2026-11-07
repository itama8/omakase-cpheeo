"""Score search against questions with known answers.

Each question lists the unit ids that answer it. A question passes when any expected id
appears in the top k results. Questions marked `out_of_scope` pass when the service
returns nothing from a manual the corpus does not contain; they document the boundary.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .service import Library


def run(questions_path: Path, db: str | None, k: int = 5, verbose: bool = False) -> int:
    lib = Library(db)
    data = yaml.safe_load(questions_path.read_text())
    available = set(lib.manuals)
    passed = scored = 0
    rank_sum = 0.0
    lines = []
    for q in data["questions"]:
        expect = q.get("expect", [])
        if not expect or not all(e.split(":")[0] in available for e in expect):
            lines.append(f"SKIP {q['id']:>4}  {q['question']}  (needs {', '.join(expect) or 'expected ids'})")
            continue
        scored += 1
        ids = [r["id"] for r in lib.search(q["question"], limit=k)["results"]]
        rank = next((i + 1 for i, uid in enumerate(ids) if uid in expect), None)
        ok = rank is not None
        passed += ok
        rank_sum += 1 / rank if rank else 0
        status = f"PASS@{rank}" if ok else "MISS  "
        lines.append(f"{status} {q['id']:>4}  {q['question']}")
        if verbose or not ok:
            lines.append(f"         expected {expect}; got {ids}")
    print("\n".join(lines))
    if scored:
        print(f"\n{passed}/{scored} answered in top {k}; MRR {rank_sum / scored:.2f}")
    return 0 if passed == scored else 1
