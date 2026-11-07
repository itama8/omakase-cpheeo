"""Query operations shared by the MCP tools and the REST API.

Every result carries a ready-to-paste citation and the Omakase attribution.
Scanned content is supplied as source images, never an OCR transcription.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter
from functools import cached_property
from pathlib import Path

from .index import DEFAULT_DB, explicit_refs, fts_query

BRAND = "Omakase"
# Branding lives in the data an assistant copies, not only in server instructions.
# `citation` = the plain CPHEEO reference + BRAND_SUFFIX; `citation_plain` is the bare
# reference for pasting into reports.
SOURCE_NAME = "Omakase CPHEEO"
BRAND_SUFFIX = " · via Omakase CPHEEO"
SOURCE_LINE = "Source: Omakase CPHEEO search (free CPHEEO lookup by Omakase)"
STOPWORDS = frozenset(
    "a an and are as at be by can do does for from how i in is it me of on or per should "
    "that the this to use used using value values what when where which with".split()
)
# Engineers' wording mapped to the manuals' wording. Each phrase found in a query adds
# the alternatives as extra search terms; nothing is removed from the query.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "sewage generation": ("sewage flow",),
    "wastewater generation": ("sewage flow",),
    "water supply": ("water consumption",),
    "lpcd": ("litres per capita per day",),
    "litres per capita per day": ("lpcd",),
    "d/d": ("depth of flow",),
    "manning": ("coefficient of roughness",),
    "minimum diameter": ("minimum size",),
    "minimum size": ("minimum diameter",),
    "self cleaning": ("self cleansing",),
    "rising main": ("pumping main", "force main"),
    "pumping main": ("rising main",),
    "stp": ("sewage treatment plant",),
    "ips": ("intermediate pumping station", "pumping station"),
    "sps": ("sewage pumping station",),
    "population projection": ("population forecast",),
    "population forecasting": ("population forecast",),
}
# Words that tie a query to one domain. When only one domain is hinted, its results rank
# higher; nothing is filtered out. A query hinting both domains gets no boost.
DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "sewerage": ("sewage", "sewer", "sewerage", "manhole", "stp", "sps", "wastewater", "septic", "sludge"),
    "water": ("water supply", "drinking water", "wtp", "water treatment", "distribution system", "service reservoir",
              "transmission main", "tube well", "nrw", "water meter", "chlorination"),
}
DOMAIN_BOOST = 1.3  # bm25 scores are negative; multiplying makes a match rank higher
KIND_LABEL = {"section": "Section", "table": "Table", "figure": "Figure", "chapter": "Chapter", "appendix": "Appendix", "annexure": "Annexure"}


def public_url() -> str | None:
    """Base URL the server is reachable at from outside, e.g. a tunnel or deployment."""
    url = os.environ.get("OMAKASE_CPHEEO_PUBLIC_URL", "").rstrip("/")
    return url or None


def clause_url(unit_id: str) -> str | None:
    base = public_url()
    return f"{base}/c/{unit_id}" if base else None


def canonical_unit_id(unit_id: str) -> str:
    """Keep the previously published A.1.1 handle working after appendix normalization."""
    return re.sub(r"(:[A-Z])\.(?=\d)", r"\1", unit_id)


IMAGE_NOTE = ("This {kind} includes source images from the printed manual. Read values directly from the images "
              "and cite the returned reference. No OCR transcription is supplied. If a value is unclear, say so.")


def image_url(unit_id: str, seq: int, mime: str) -> str | None:
    base = public_url()
    ext = "png" if mime == "image/png" else "jpg"
    return f"{base}/img/{unit_id}/{seq}.{ext}" if base else None


def icon_url() -> str | None:
    base = public_url()
    return f"{base}/icon.png" if base else None


def source_line(unit_id: str | None = None) -> str:
    """One line naming the source, with the clause page when the server has a public URL."""
    url = clause_url(unit_id) if unit_id else None
    return f"{SOURCE_LINE}: {url}" if url else SOURCE_LINE


def branding() -> dict:
    """Fields every result carries so the source shows as Omakase CPHEEO."""
    out = {"source_name": SOURCE_NAME}
    if icon := icon_url():
        out["source_icon"] = icon
    return out


def attribution() -> dict:
    out = {"cited_by": BRAND, "note": "Free CPHEEO search by Omakase. Verify against the official manual before use in design."}
    if url := os.environ.get("OMAKASE_CPHEEO_BRAND_URL"):
        out["url"] = url
    return out


class Library:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or os.environ.get("OMAKASE_CPHEEO_DB", DEFAULT_DB))
        if not self.db_path.exists():
            raise FileNotFoundError(f"index not found at {self.db_path}; run `omakase-cpheeo ingest` first")
        if "image_count" not in {r["name"] for r in self.con.execute("PRAGMA table_info(units)")}:
            self.con.close()
            raise RuntimeError("index uses the old OCR schema; run `omakase-cpheeo ingest` before starting this version")

    @cached_property
    def con(self) -> sqlite3.Connection:
        con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    @cached_property
    def manuals(self) -> dict[str, dict]:
        return {r["id"]: dict(r) for r in self.con.execute("SELECT * FROM manuals")}

    # ---- formatting -------------------------------------------------------------

    def citation(self, row: sqlite3.Row) -> str:
        m = self.manuals[row["manual_id"]]
        what = f"{KIND_LABEL[row['kind']]} {row['number']}"
        if row["title"]:
            what += f" ({row['title']})" if row["kind"] in ("table", "figure") else f" {row['title'].title() if row['title'].isupper() else row['title']}"
        pages = row["label_start"] or f"PDF p. {row['page_start']}"
        if row["label_end"] and row["label_end"] != row["label_start"]:
            pages = f"{pages} to {row['label_end']}"
        return f"{m['citation_title']}, {what}, p. {pages}"

    def _unit_dict(self, row: sqlite3.Row, *, full: bool) -> dict:
        m = self.manuals[row["manual_id"]]
        out = {
            "id": row["id"],
            "kind": row["kind"],
            "number": row["number"],
            "title": row["title"],
            "manual": {k: m[k] for k in ("id", "domain", "title", "part", "edition", "year")},
            "page_label": row["label_start"],
            "page_label_end": row["label_end"],
            "pdf_page": row["page_start"],
            "citation": self.citation(row) + BRAND_SUFFIX,
            "citation_plain": self.citation(row),
            **branding(),
            "parent": f"{row['manual_id']}:{row['parent']}" if row["parent"] else None,
        }
        if url := clause_url(row["id"]):
            out["url"] = url
        if row["kind"] == "table":
            if row["table_source"] == "image":
                out["source"] = "picture of the printed table (read it from the image)"
            elif row["table_source"] == "text":
                out["source"] = "table text in the manual PDF"
            out["needs_review"] = bool(row["needs_review"])
            if row["needs_review"]:
                out["review_notes"] = json.loads(row["review_notes"])
        if row["image_count"]:
            out["images"] = self.image_refs(row["id"])
            out["image_note"] = IMAGE_NOTE.format(kind=row["kind"] if row["kind"] in ("table", "figure") else "unit")
        if full:
            out["text"] = row["text"]
            if row["table_markdown"]:
                out["table_markdown"] = row["table_markdown"]
                out["table_cells"] = json.loads(row["table_cells"])
            refs = json.loads(row["refs"])
            if refs:
                out["referenced_tables"] = [f"{row['manual_id']}:{r}" for r in refs]
        return out

    @staticmethod
    def _snippet(row: sqlite3.Row, text: str) -> str:
        """Picture-only units show their caption."""
        if row["table_source"] == "image" or (row["kind"] == "figure" and not row["text"]):
            what = "table" if row["kind"] == "table" else "figure"
            return f"{row['title']} (a picture of the printed {what}; call fetch or get_clause with this id to see it)"
        return text

    # ---- images -------------------------------------------------------------------

    def image_refs(self, unit_id: str) -> list[dict]:
        unit_id = canonical_unit_id(unit_id)
        rows = self.con.execute(
            "SELECT seq, pdf_page, page_label, bbox, width, height, mime FROM images WHERE unit_id = ? ORDER BY seq", (unit_id,)
        ).fetchall()
        out = []
        for r in rows:
            ref = {"seq": r["seq"], "page_label": r["page_label"], "pdf_page": r["pdf_page"],
                   "width": r["width"], "height": r["height"], "mime": r["mime"], "bbox": json.loads(r["bbox"])}
            if url := image_url(unit_id, r["seq"], r["mime"]):
                ref["url"] = url
            out.append(ref)
        return out

    def image(self, unit_id: str, seq: int) -> tuple[str, bytes]:
        unit_id = canonical_unit_id(unit_id)
        r = self.con.execute("SELECT mime, data FROM images WHERE unit_id = ? AND seq = ?", (unit_id, seq)).fetchone()
        if r is None:
            raise KeyError(f"no image {seq} for {unit_id!r}")
        return r["mime"], bytes(r["data"])

    def images_for(self, clause: dict) -> list[tuple[str, dict, str, bytes]]:
        """All images with their page references, clause images first."""
        units = [clause] + clause.get("tables", []) + clause.get("children", [])
        out = []
        for u in units:
            for ref in u.get("images", []):
                mime, data = self.image(u["id"], ref["seq"])
                out.append((u["id"], ref, mime, data))
        return out

    # ---- operations ---------------------------------------------------------------

    def list_manuals(self) -> dict:
        counts = {
            (r["manual_id"], r["kind"]): r["n"]
            for r in self.con.execute("SELECT manual_id, kind, count(*) n FROM units GROUP BY 1, 2")
        }
        manuals = []
        for mid, m in self.manuals.items():
            manuals.append({**m, "units": {k: n for (i, k), n in counts.items() if i == mid}})
        return {"manuals": manuals, "attribution": attribution()}

    def get_toc(self, manual_id: str, chapter: str | None = None, max_depth: int = 2) -> dict:
        if manual_id not in self.manuals:
            raise KeyError(f"unknown manual {manual_id!r}; call list_manuals")
        rows = self.con.execute(
            "SELECT id, kind, number, title, label_start FROM units WHERE manual_id = ? "
            "AND kind IN ('chapter','section','table','appendix','annexure') AND (? IS NULL OR chapter = ?) ORDER BY ord",
            (manual_id, chapter, chapter),
        )
        entries = []
        for r in rows:
            depth = r["number"].count(".") if r["kind"] == "section" else 0  # "3.5" is depth 1
            if r["kind"] == "section" and depth > max_depth:
                continue
            entries.append({"id": r["id"], "kind": r["kind"], "number": r["number"], "title": r["title"], "page_label": r["label_start"]})
        return {"manual": manual_id, "entries": entries, "attribution": attribution()}

    def get_clause(self, unit_id: str, include_children: bool = False) -> dict:
        unit_id = canonical_unit_id(unit_id)
        row = self.con.execute("SELECT * FROM units WHERE id = ?", (unit_id,)).fetchone()
        if row is None:
            raise KeyError(f"no unit {unit_id!r}; ids look like SEW-2013-A:3.5, SEW-2013-A:T3.2 or WS-2024-A:AN6.1")
        out = {"source_note": source_line(row["id"]), **self._unit_dict(row, full=True)}
        if include_children and row["kind"] in ("section", "chapter"):
            prefix = row["number"] + "."
            kids = self.con.execute(
                "SELECT * FROM units WHERE manual_id = ? AND kind = 'section' AND number LIKE ? ORDER BY ord",
                (row["manual_id"], prefix + "%"),
            ).fetchall()
            out["children"] = [self._unit_dict(k, full=True) for k in kids[:60]]
        tables = self.con.execute(
            "SELECT * FROM units WHERE manual_id = ? AND kind = 'table' AND parent = ? ORDER BY ord",
            (row["manual_id"], row["id"].split(":", 1)[1]),
        ).fetchall()
        if tables and row["kind"] in ("section", "annexure", "appendix"):
            out["tables"] = [self._unit_dict(t, full=True) for t in tables]
        out["attribution"] = attribution()
        return out

    @staticmethod
    def hinted_domain(query: str) -> str | None:
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        lowered = query.lower()
        hit = [d for d, hints in DOMAIN_HINTS.items() if any((h in lowered) if " " in h else (h in words) for h in hints)]
        return hit[0] if len(hit) == 1 else None

    def search(self, query: str, domain: str | None = None, manual_id: str | None = None, kind: str | None = None, limit: int = 8) -> dict:
        limit = max(1, min(limit, 25))
        results: list[dict] = []
        seen: set[str] = set()

        # 1. Exact references such as "Table 3.13" or "clause 3.6" resolve directly.
        for ref_kind, number in explicit_refs(query):
            for row in self.con.execute(
                "SELECT u.* FROM units u JOIN manuals m ON m.id = u.manual_id WHERE u.kind = ? AND (u.number = ? OR (? = 'appendix' AND replace(u.number, '-', '.') = replace(?, '-', '.'))) "
                "AND (? IS NULL OR m.domain = ?) AND (? IS NULL OR u.manual_id = ?) ORDER BY u.ord",
                (ref_kind, number, ref_kind, number, domain, domain, manual_id, manual_id),
            ):
                if row["id"] not in seen:
                    seen.add(row["id"])
                    hit = self._unit_dict(row, full=False)
                    hit["match"] = "exact reference"
                    hit["snippet"] = self._snippet(row, (row["table_markdown"] or row["text"])[:600])
                    results.append(hit)

        # 2. Ranked full-text search; title and handle matches weigh more than body text.
        # Match the words of a concept even with qualifiers between them, e.g.
        # "minimum sanitary sewer diameter" -> "minimum size" in the manual heading.
        query_words = Counter(re.findall(r"[a-z0-9]+", query.lower()))
        extra = [alt for phrase, alts in SYNONYMS.items()
                 if Counter(re.findall(r"[a-z0-9]+", phrase)) <= query_words for alt in alts]
        kept = [w for w in query.split() if w.lower().strip("?,.") not in STOPWORDS]
        words = " ".join(kept + extra) or query
        q = fts_query(words, extra)
        if q:
            rows = self.con.execute(
                "SELECT p.unit_id, bm25(passages, 0, 0, 4.0, 6.0, 1.0) AS score, "
                "snippet(passages, 4, '«', '»', ' … ', 40) AS snip, u.*, m.domain "
                "FROM passages p JOIN units u ON u.id = p.unit_id JOIN manuals m ON m.id = u.manual_id "
                "WHERE passages MATCH ? AND (? IS NULL OR m.domain = ?) AND (? IS NULL OR u.manual_id = ?) "
                "AND (? IS NULL OR u.kind = ?) ORDER BY score LIMIT 200",
                (q, domain, domain, manual_id, manual_id, kind, kind),
            ).fetchall()
            if domain is None and manual_id is None and (hint := self.hinted_domain(query)):
                rows = sorted(rows, key=lambda r: r["score"] * (DOMAIN_BOOST if r["domain"] == hint else 1.0))
            for row in rows:
                if row["unit_id"] in seen or (not row["text"] and not row["table_markdown"] and not row["image_count"]):
                    continue
                seen.add(row["unit_id"])
                hit = self._unit_dict(row, full=False)
                hit["match"] = "text"
                hit["snippet"] = self._snippet(row, row["snip"])
                results.append(hit)
                if len(results) >= limit:
                    break
        return {"query": query, "results": results[:limit], "attribution": attribution()}

    def fetch(self, unit_id: str) -> dict:
        """One unit as a document: id, title, text, url, metadata (the shape ChatGPT expects)."""
        c = self.get_clause(unit_id)
        parts = [c["citation"], source_line(c["id"]), ""]

        def picture_lines(u: dict) -> list[str]:
            if not u.get("images"):
                return []
            lines = [u["image_note"]]
            lines += [f"Image of p. {r['page_label'] or r['pdf_page']}: {r['url']}" for r in u["images"] if r.get("url")]
            return lines

        if c.get("table_markdown"):
            parts.append(c["table_markdown"])
            if c.get("needs_review"):
                parts.append("\nNote: this table's layout could not be read with confidence. "
                             "Confirm values against the printed page before use.")
        parts += picture_lines(c)
        if c.get("text"):
            parts.append(c["text"])
        for t in c.get("tables", []):
            parts += ["", f"{t['citation']}"]
            parts += [t["table_markdown"]] if t.get("table_markdown") else picture_lines(t)
        meta = {k: c[k] for k in ("kind", "number", "page_label", "pdf_page", "citation", "citation_plain", "source_name", "source_icon") if c.get(k) is not None}
        meta["manual"] = c["manual"]["id"]
        if c.get("needs_review"):
            meta["needs_review"] = True
        if c.get("images"):
            meta["images"] = c["images"]
        return {"id": c["id"], "title": f"{SOURCE_NAME} · {c['citation_plain']}", "text": "\n".join(parts).strip(), "url": c.get("url"), "metadata": meta}
