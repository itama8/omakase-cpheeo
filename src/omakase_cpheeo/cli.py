"""Command line: ingest the manuals, query the index, run the server, run the eval."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .index import DEFAULT_DB


def cmd_ingest(args: argparse.Namespace) -> None:
    from . import index
    from .corpus import MANUALS, sources_dir
    from .extract import open_clean
    from .structure import build_units

    selected = [m for m in MANUALS if not args.manual or m.id in args.manual]
    units = []
    for m in selected:
        path = sources_dir() / m.file
        t0 = time.time()
        print(f"[{m.id}] {path}", file=sys.stderr)

        def progress(n: int, total: int) -> None:
            if n % 100 == 0:
                print(f"  page {n}/{total}", file=sys.stderr)

        got = build_units(m, open_clean(path), progress=progress)
        print(f"  {len(got)} units in {time.time() - t0:.0f}s", file=sys.stderr)
        units.extend(got)
    db = index.build(units, tuple(selected), Path(args.db))
    review = [
        {"id": u.id, "title": u.title, "page_label": u.label_start, "pdf_page": u.page_start, "notes": u.review_notes}
        for u in units
        if u.needs_review
    ]
    review_path = Path(args.db).with_name("review.json")
    review_path.write_text(json.dumps(review, indent=1))
    print(f"index: {db}\nreview list: {review_path} ({len(review)} units)", file=sys.stderr)


def cmd_search(args: argparse.Namespace) -> None:
    from .service import Library

    out = Library(args.db).search(" ".join(args.query), domain=args.domain, limit=args.limit)
    for r in out["results"]:
        flag = " [check table]" if r.get("needs_review") else ""
        print(f"{r['id']:22} {r['citation']}{flag}\n    {r['snippet'][:220]!r}")


def cmd_clause(args: argparse.Namespace) -> None:
    from .service import Library

    print(json.dumps(Library(args.db).get_clause(args.id, include_children=args.children), indent=1, ensure_ascii=False))


def cmd_serve(args: argparse.Namespace) -> None:
    from .server import serve

    serve(host=args.host, port=args.port, db=args.db)


def cmd_eval(args: argparse.Namespace) -> None:
    from .evaluate import run

    sys.exit(run(Path(args.questions), args.db, k=args.k, verbose=args.verbose))


def main() -> None:
    p = argparse.ArgumentParser(prog="omakase-cpheeo")
    p.add_argument("--db", default=str(DEFAULT_DB))
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("ingest", help="parse the manuals and build the index")
    s.add_argument("--manual", action="append", help="manual id to ingest (repeatable); default all")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("search")
    s.add_argument("query", nargs="+")
    s.add_argument("--domain")
    s.add_argument("--limit", type=int, default=6)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("clause")
    s.add_argument("id")
    s.add_argument("--children", action="store_true")
    s.set_defaults(func=cmd_clause)

    s = sub.add_parser("serve", help="run the MCP + REST server")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("eval", help="score search against the question set")
    s.add_argument("--questions", default=str(Path(__file__).resolve().parents[2] / "eval" / "questions.yaml"))
    s.add_argument("-k", type=int, default=5)
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(func=cmd_eval)

    args = p.parse_args()
    args.func(args)
