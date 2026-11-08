"""Score search against questions with known answers.

Each question lists the unit ids that answer it. A question passes when any expected id
appears in the top k results. Questions marked `out_of_scope` pass when the service
returns nothing from a manual the corpus does not contain; they document the boundary.

A file with a `groups:` key holds paraphrase groups instead: several phrasings of one
engineering question, all answered by the same units. A group is scored on its
worst-ranked phrasing, because an assistant only sees the phrasing it happened to write.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .service import Library

# Paraphrase ranks are looked up this deep so a near miss shows as rank 7, not "miss".
DEEP = 25


def run(questions_path: Path, db: str | None, k: int = 5, verbose: bool = False) -> int:
    lib = Library(db)
    data = yaml.safe_load(questions_path.read_text())
    if "groups" in data:
        return run_groups(lib, data["groups"], k=k, verbose=verbose)
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


def phrasing_text(p: str | dict) -> tuple[str, str]:
    """A phrasing is a bare string or {q: ..., style: ...}."""
    return (p, "") if isinstance(p, str) else (p["q"], p.get("style", ""))


def score_groups(lib: Library, groups: list[dict]) -> list[dict]:
    """Rank of the first expected id for every phrasing (None beyond DEEP)."""
    out = []
    for g in groups:
        rows = []
        for p in g["phrasings"]:
            text, style = phrasing_text(p)
            ids = [r["id"] for r in lib.search(text, limit=DEEP)["results"]]
            rank = next((i + 1 for i, uid in enumerate(ids) if uid in g["expect"]), None)
            rows.append({"q": text, "style": style, "rank": rank, "top": ids[:5]})
        out.append({**g, "scored": rows})
    return out


def _rank_label(rank: int | None) -> str:
    return str(rank) if rank else f">{DEEP}"


def run_groups(lib: Library, groups: list[dict], k: int = 5, verbose: bool = False) -> int:
    available = set(lib.manuals)
    usable = [g for g in groups if all(e.split(":")[0] in available for e in g["expect"])]
    for g in groups:
        if g not in usable:
            print(f"SKIP {g['id']:>4}  {g['target']}  (needs {', '.join(g['expect'])})")
    scored = score_groups(lib, usable)
    group_pass = 0
    worst_rr = phr_rr = 0.0
    n_phr = hit1 = hitk = 0
    for g in scored:
        ranks = [r["rank"] for r in g["scored"]]
        worst = None if None in ranks else max(ranks)
        ok = worst is not None and worst <= k
        group_pass += ok
        worst_rr += 1 / worst if worst else 0
        h1 = sum(r == 1 for r in ranks)
        hk = sum(r is not None and r <= k for r in ranks)
        n_phr += len(ranks)
        hit1 += h1
        hitk += hk
        phr_rr += sum(1 / r for r in ranks if r)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {g['id']:>4}  worst {_rank_label(worst):>3}  hit@1 {h1}/{len(ranks)}  hit@{k} {hk}/{len(ranks)}  {g['target']}")
        for r in g["scored"]:
            miss = r["rank"] is None or r["rank"] > k
            if verbose or miss:
                style = f"[{r['style']}] " if r["style"] else ""
                print(f"        {_rank_label(r['rank']):>3}  {style}{r['q']}")
                if miss:
                    print(f"             expected {g['expect']}; got {r['top']}")
    n = len(scored)
    if n:
        print(f"\n{group_pass}/{n} groups with every phrasing in top {k}; worst-rank MRR {worst_rr / n:.2f}")
        print(f"phrasings: hit@1 {hit1}/{n_phr} ({hit1 / n_phr:.0%}), hit@{k} {hitk}/{n_phr} ({hitk / n_phr:.0%}), MRR {phr_rr / n_phr:.2f}")
    return 0 if group_pass == n else 1
