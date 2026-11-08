"""SQLite index: one row per citable unit, plus an FTS5 table of searchable passages."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from .corpus import MANUALS, Manual
from .structure import Unit

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "build" / "cpheeo.sqlite"
PASSAGE_CHARS = 1500
PASSAGE_OVERLAP = 200

SCHEMA = """
CREATE TABLE manuals (
  id TEXT PRIMARY KEY, domain TEXT, title TEXT, part TEXT, edition TEXT, year INTEGER, citation_title TEXT
);
CREATE TABLE units (
  id TEXT PRIMARY KEY, manual_id TEXT, kind TEXT, number TEXT, title TEXT, chapter TEXT, parent TEXT,
  page_start INTEGER, page_end INTEGER, label_start TEXT, label_end TEXT,
  text TEXT, table_markdown TEXT, table_cells TEXT, table_source TEXT, image_count INTEGER, needs_review INTEGER, review_notes TEXT, refs TEXT,
  ord INTEGER
);
-- Crops of the printed page (table and figure pictures) that assistants read directly.
CREATE TABLE images (
  unit_id TEXT, seq INTEGER, pdf_page INTEGER, page_label TEXT, bbox TEXT,
  width INTEGER, height INTEGER, mime TEXT, data BLOB, PRIMARY KEY (unit_id, seq)
);
CREATE INDEX units_manual_number ON units(manual_id, number);
CREATE INDEX units_parent ON units(manual_id, parent);
CREATE VIRTUAL TABLE passages USING fts5(
  unit_id UNINDEXED, seq UNINDEXED, handle, title, body,
  tokenize = 'porter unicode61'
);
"""


def handle_tokens(unit: Unit) -> str:
    """Searchable handle for a unit's number: table 3.2 -> "t3x2 table"."""
    n = unit.number.replace(".", "x")
    prefix = {"table": "t", "figure": "f", "chapter": "ch", "appendix": "a", "annexure": "an"}.get(unit.kind, "s")
    return f"{prefix}{n} {unit.kind}"


def passages_of(unit: Unit) -> list[str]:
    body = unit.table_markdown or unit.text
    if unit.kind == "table" and unit.text:
        body = f"{body}\n{unit.text}"
    if not body and unit.images:  # a figure: its caption is the searchable part
        body = unit.title
    if len(body) <= PASSAGE_CHARS:
        return [body]
    out, start = [], 0
    while start < len(body):
        end = min(len(body), start + PASSAGE_CHARS)
        if end < len(body):  # end on a sentence or line boundary when one is near
            cut = max(body.rfind(". ", start, end), body.rfind("\n", start, end))
            if cut > start + PASSAGE_CHARS // 2:
                end = cut + 1
        out.append(body[start:end])
        if end >= len(body):
            break
        start = max(end - PASSAGE_OVERLAP, start + 1)
    return out


def build(units: list[Unit], manuals: tuple[Manual, ...] = MANUALS, db_path: Path = DEFAULT_DB, *, transcription_records: Path | None = None) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    for m in manuals:
        con.execute(
            "INSERT INTO manuals VALUES (?,?,?,?,?,?,?)",
            (m.id, m.domain, m.title, m.part, m.edition, m.year, m.citation_title),
        )
    by_id = {u.id: u for u in units}
    appendix_groups = {f"{u.manual_id}:{u.parent}" for u in units if u.kind == "appendix" and u.parent}

    def breadcrumb(u: Unit) -> str:
        """Parent headings, so "2.6.1 General Considerations" is found as population forecast."""
        names, seen = [], set()
        parent = u.parent
        while parent and len(names) < 3:
            p = by_id.get(f"{u.manual_id}:{parent}")
            if p is None or p.id in seen:
                break
            seen.add(p.id)
            names.append(p.title)
            parent = p.parent
        return " ".join(names)
    for i, u in enumerate(units):
        con.execute(
            "INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                u.id, u.manual_id, u.kind, u.number, u.title, u.chapter, u.parent,
                u.page_start, u.page_end, u.label_start, u.label_end,
                u.text, u.table_markdown, json.dumps(u.table_cells), u.table_source, len(u.images), int(u.needs_review),
                json.dumps(u.review_notes), json.dumps(u.references), i,
            ),
        )
        for seq, im in enumerate(u.images):
            con.execute(
                "INSERT INTO images VALUES (?,?,?,?,?,?,?,?,?)",
                (u.id, seq, im["pdf_page"], im["page_label"], json.dumps(im["bbox"]), im["width"], im["height"], im["mime"], im["data"]),
            )
        # Legacy group handles remain fetchable, but keyword search should not return
        # the same worked example twice as both a group and its actual A/B sheet.
        if u.id in appendix_groups:
            continue
        context = breadcrumb(u)
        for seq, text in enumerate(passages_of(u)):
            con.execute(
                "INSERT INTO passages VALUES (?,?,?,?,?)",
                (u.id, seq, handle_tokens(u), f"{u.title} {context}".strip(), text),
            )
    if transcription_records is not None:
        from .transcriptions import apply
        apply(con, transcription_records)
    con.commit()
    con.execute("INSERT INTO passages(passages) VALUES ('optimize')")
    con.commit()
    con.close()
    tmp.replace(db_path)
    return db_path


_WORD = re.compile(r"[A-Za-z0-9]+")
_NUMBERED_REF = re.compile(
    r"\b(equation|eq|table|tab|fig|figure|section|sec|clause|para|paragraph|chapter|ch|appendix|app|annexure|annex)\.?\s*"
    r"([A-Z]\s*[.-]?\s*\d+(?:[.-]\s*\d+)*(?:\s*[A-Z]\b)?(?:[.-]\s*\d+)*|AA\b|A\b|\d+(?:[.-]\d+)*[A-Za-z]?)", re.I,
)


def fts_query(text: str, phrases: list[str] = ()) -> str:
    """Turn free text into an FTS5 OR-query of quoted terms (no operator injection).

    Each phrase (e.g. a synonym such as "sewage flow") is added as an exact-phrase term,
    so units that use the whole phrase outrank units that only share common words.
    """
    terms = [t for t in _WORD.findall(text.lower()) if len(t) > 1 or t.isdigit()]
    quoted = [f'"{t}"' for t in dict.fromkeys(terms)]
    for ph in dict.fromkeys(phrases):
        words = _WORD.findall(ph.lower())
        if len(words) > 1:
            quoted.append('"' + " ".join(words) + '"')
    return " OR ".join(quoted)


def explicit_refs(text: str) -> list[tuple[str, str]]:
    """Find "Table 3.2", "clause 3.6", "para 3.25" style references in a query."""
    out = []
    for kind, number in _NUMBERED_REF.findall(text):
        k = kind.lower()
        kind = "equation" if k in ("eq", "equation") else "table" if k.startswith("tab") else "figure" if k.startswith("fig") else "chapter" if k.startswith("ch") else "annexure" if k.startswith("annex") else "appendix" if k.startswith("app") else "section"
        number = re.sub(r"\s+", "", number).upper()
        number = re.sub(r"^([A-Z])\.(?=\d)", r"\1", number)
        if number[0].isdigit():
            number = number.replace("-", ".")
        out.append((kind, number))
    return out
