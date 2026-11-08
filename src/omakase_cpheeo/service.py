"""Query operations shared by the MCP tools and the REST API.

Every result carries a ready-to-paste citation and the Omakase attribution.
Scanned content retains source images alongside explicitly verified visual transcriptions.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter
from functools import cached_property
from pathlib import Path

from .corpus import UNINDEXED
from .index import DEFAULT_DB, explicit_refs, fts_query
from .quality import TextDefects, annotate, enumeration_gaps

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
DESIGN_INTENT = re.compile(r"\b(design|norms?|criteria|standards?|recommended|minimum|maximum|permissible|requirements?|limits?)\b", re.I)
EXAMPLE_HEADING = re.compile(r"\b(examples?|illustrat\w*|worked|sample calculations?)\b", re.I)
SEARCH_KINDS = ("section", "table", "figure", "equation", "appendix", "annexure", "chapter")
KIND_LABEL = {"equation": "Equation", "section": "Section", "table": "Table", "figure": "Figure", "chapter": "Chapter", "appendix": "Appendix", "annexure": "Annexure"}


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
              "and cite the returned reference. Verified transcriptions, when present, identify their exact source regions. "
              "Other regions have not been verified. If a value is unclear, say so.")


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


class ToolInputError(Exception):
    """A caller mistake an agent can recover from: a stable code, the reason and what to try next."""

    def __init__(self, code: str, message: str, *, suggestions: list[str] | tuple[str, ...] = (), recovery: str | None = None):
        super().__init__(message)
        self.code, self.message, self.suggestions, self.recovery = code, message, list(suggestions), recovery

    def __str__(self) -> str:  # KeyError would otherwise wrap the message in quotes
        return self.message

    def to_dict(self) -> dict:
        err = {"code": self.code, "message": self.message}
        if self.suggestions:
            err["suggestions"] = self.suggestions
        if self.recovery:
            err["recovery"] = self.recovery
        return {"error": err, "attribution": attribution()}


class UnknownId(ToolInputError, KeyError):
    """No such unit or manual. A KeyError so REST handlers return 404."""


class InvalidArgument(ToolInputError, ValueError):
    """An argument outside its allowed values."""


EVIDENCE_PRECEDENCE = (
    "`text` is the PDF's extracted text layer; it is not visually verified and can garble mathematical notation "
    "or drop lines. Where a verified transcription (`verified_text`, or `equations[].verified_text`) covers the same "
    "content, the verified transcription takes precedence. `reading_text`, when present, is `text` with known "
    "extraction defects and possible omissions marked inline; `text` is kept unchanged for traceability."
)


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

    @cached_property
    def has_transcriptions(self) -> bool:
        return bool(self.con.execute("SELECT 1 FROM sqlite_master WHERE name='transcriptions'").fetchone())

    def transcription_records(self, unit_id: str) -> list[dict]:
        if not self.has_transcriptions:
            return []
        return [json.loads(r[0]) for r in self.con.execute(
            "SELECT payload FROM transcriptions WHERE unit_id=? ORDER BY id", (unit_id,))]

    def transcriptions(self, unit_id: str) -> list[dict]:
        return [r for r in self.transcription_records(unit_id) if r['state']=='verified']

    # ---- formatting -------------------------------------------------------------

    def citation(self, row: sqlite3.Row) -> str:
        m = self.manuals[row["manual_id"]]
        what = f"{KIND_LABEL[row['kind']]} {row['number']}"
        if row["title"]:
            what += f" ({row['title']})" if row["kind"] in ("table", "figure") else f" {row['title'].title() if row['title'].isupper() else row['title']}"
        transcripts = self.transcriptions(row['id'])
        if transcripts:
            regions = [reg for t in transcripts for reg in t['regions']]
            first, last = min(regions,key=lambda r:r['pdf_page']), max(regions,key=lambda r:r['pdf_page'])
            pages = first['page_label'] or f"PDF p. {first['pdf_page']}"
            if last['pdf_page'] != first['pdf_page']:
                pages += ' to ' + (last['page_label'] or f"PDF p. {last['pdf_page']}")
        else:
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
        transcripts = self.transcriptions(row['id'])
        if transcripts:
            out['transcription_status'] = 'verified'
            out['verification_scope'] = 'Visual transcription fidelity; printed engineering correctness is not validated.'
            out['source'] = 'visually transcribed and rechecked against the printed source; source errors are retained'
            out['transcription_pages'] = [{'pdf_page':reg['pdf_page'],'page_label':reg['page_label']} for t in transcripts for reg in t['regions']]
            first = min(out['transcription_pages'],key=lambda reg:reg['pdf_page'])
            last = max(out['transcription_pages'],key=lambda reg:reg['pdf_page'])
            out.update(pdf_page=first['pdf_page'],pdf_page_end=last['pdf_page'],page_label=first['page_label'],page_label_end=last['page_label'])
            if full:
                from .transcriptions import readable
                out['verified_transcriptions'] = transcripts
                out['verified_text'] = '\n\n'.join(readable(t) for t in transcripts)
        pending = [r for r in self.transcription_records(row['id']) if r['state']!='verified']
        if pending:
            out['transcription_status'] = pending[0]['state'] if len(pending)==1 else 'incomplete'
            out['transcription_notes'] = [note for r in pending for note in r.get('notes',[])]
            if full:
                out['unverified_regions'] = [{k:r[k] for k in ('id','state','regions','raw_visible_text','notes') if k in r} for r in pending]
        quality = self.text_quality(row)
        if full:
            out["text"] = row["text"]
            if quality:
                out["text_quality"] = quality
                out["reading_text"] = annotate(row["text"], quality.get("known_defects", []), quality["_gaps"])
                del quality["_gaps"]
            if row["table_markdown"]:
                out["table_markdown"] = row["table_markdown"]
                out["table_cells"] = json.loads(row["table_cells"])
            refs = json.loads(row["refs"])
            if refs:
                out["referenced_tables"] = [f"{row['manual_id']}:{r}" for r in refs]
        elif quality:
            flags = []
            if quality.get("known_defects"):
                flags.append("known_extraction_defects")
            if quality.get("possible_omissions"):
                flags.append("possible_omissions")
            out["quality_flags"] = flags
        return out

    @cached_property
    def defects(self) -> TextDefects:
        return TextDefects()

    def text_quality(self, row: sqlite3.Row) -> dict:
        """Known defects and likely omissions in a unit's extracted text; empty when none are known."""
        text = row["text"] or ""
        if not text:
            return {}
        defects = self.defects.for_unit(row["id"], text)
        gaps = enumeration_gaps(text)
        if not defects and not gaps:
            return {}
        out: dict = {"status": "extracted text with known problems; see notes", "_gaps": gaps}
        if defects:
            out["known_defects"] = defects
        if gaps:
            out["possible_omissions"] = [g.to_dict() for g in gaps]
        return out

    def _snippet(self, row: sqlite3.Row, text: str) -> str:
        """Picture-only units show their caption."""
        if self.transcriptions(row["id"]):
            from .transcriptions import readable
            return text or readable(self.transcriptions(row["id"])[0])[:600]
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
        out, seen = [], set()
        def visit(u):
            for ref in u.get('images', []):
                key = (u['id'],ref['seq'])
                if key not in seen:
                    seen.add(key)
                    mime, data = self.image(*key)
                    out.append((u['id'],ref,mime,data))
            for key in ('tables','equations','children'):
                for child in u.get(key,[]):
                    visit(child)
        visit(clause)
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
        not_indexed = [{"id": u.id, "domain": u.domain, "title": u.title, "year": u.year, "status": u.status} for u in UNINDEXED]
        return {"manuals": manuals, "not_indexed": not_indexed, "attribution": attribution()}

    def get_toc(self, manual_id: str, chapter: str | None = None, max_depth: int = 2) -> dict:
        if manual_id not in self.manuals:
            raise UnknownId("unknown_manual", f"no indexed manual {manual_id!r}", suggestions=list(self.manuals),
                            recovery="Call list_manuals for the indexed manuals and their ids.")
        rows = self.con.execute(
            "SELECT id, kind, number, title, label_start FROM units WHERE manual_id = ? "
            "AND kind IN ('chapter','section','table','equation','appendix','annexure') AND (? IS NULL OR chapter = ?) ORDER BY ord",
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
            raise self.unknown_unit(unit_id)
        out = {"source_note": source_line(row["id"]), **self._unit_dict(row, full=True)}
        if include_children and row["kind"] in ("section", "chapter"):
            prefix = row["number"] + "."
            kids = self.con.execute(
                "SELECT * FROM units WHERE manual_id = ? AND kind = 'section' AND number LIKE ? ORDER BY ord",
                (row["manual_id"], prefix + "%"),
            ).fetchall()
            out["children"] = [self._unit_dict(k, full=True) for k in kids[:60]]
            for child in out['children']:
                eqs = self.con.execute("SELECT * FROM units WHERE manual_id=? AND kind='equation' AND parent=? ORDER BY number",
                                        (row['manual_id'],child['id'].split(':',1)[1])).fetchall()
                if eqs:
                    child['equations'] = [self._unit_dict(e,full=True) for e in eqs]
        tables = self.con.execute(
            "SELECT * FROM units WHERE manual_id = ? AND kind = 'table' AND parent = ? ORDER BY ord",
            (row["manual_id"], row["id"].split(":", 1)[1]),
        ).fetchall()
        if tables and row["kind"] in ("section", "annexure", "appendix"):
            out["tables"] = [self._unit_dict(t, full=True) for t in tables]
        equations = self.con.execute(
            "SELECT * FROM units WHERE manual_id=? AND kind='equation' AND parent=? ORDER BY ord,number",
            (row['manual_id'], row['id'].split(':',1)[1]),
        ).fetchall()
        if equations:
            out['equations'] = [self._unit_dict(e, full=True) for e in equations]
        if out.get("text") or any(c.get("text") for c in out.get("children", [])):
            out["evidence_precedence"] = EVIDENCE_PRECEDENCE
        out["attribution"] = attribution()
        return out

    def unknown_unit(self, unit_id: str) -> UnknownId:
        """An unknown id, with the nearest real ids and what to call next."""
        manual_id, _, tail = unit_id.partition(":")
        recovery = "Call search with the clause number or topic, or get_toc(manual, chapter) to list valid ids."
        if not tail:
            core = re.search(r"\d+(?:[.-]\d+)*", unit_id)
            rows = self.con.execute("SELECT id FROM units WHERE number = ? ORDER BY ord LIMIT 5", (core.group(0),)).fetchall() if core else []
            return UnknownId("unknown_id", f"no unit {unit_id!r}: ids are '<manual>:<handle>', e.g. SEW-2013-A:3.5, SEW-2013-A:T3.2 or WS-2024-A:AN6.1",
                             suggestions=[r[0] for r in rows], recovery=recovery)
        if manual_id not in self.manuals:
            return UnknownId("unknown_manual", f"no indexed manual {manual_id!r} in id {unit_id!r}",
                             suggestions=list(self.manuals), recovery="Call list_manuals for the indexed manuals and their ids.")
        core = re.search(r"\d+(?:[.-]\d+)*", tail)
        suggestions: list[str] = []
        if core:
            number = core.group(0)
            # The same number under another kind (T3.2 asked as 3.2), then the nearest enclosing clause.
            suggestions = [r[0] for r in self.con.execute(
                "SELECT id FROM units WHERE manual_id = ? AND number = ? ORDER BY ord LIMIT 5", (manual_id, number))]
            # Then units under the nearest enclosing number with the same handle letters (T3.99 -> tables T3.*).
            letters = tail[:core.start()]
            parts = re.split(r"[.-]", number)
            while not suggestions and len(parts) > 1:
                parts.pop()
                handle = f"{manual_id}:{letters}{'.'.join(parts)}"
                suggestions = [r[0] for r in self.con.execute(
                    "SELECT id FROM units WHERE manual_id = ? AND (id = ? OR id LIKE ?) ORDER BY ord LIMIT 5",
                    (manual_id, handle, handle + ".%"))]
        return UnknownId("unknown_id", f"no unit {unit_id!r} in {manual_id}", suggestions=suggestions, recovery=recovery)

    @staticmethod
    def hinted_domain(query: str) -> str | None:
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        lowered = query.lower()
        hit = [d for d, hints in DOMAIN_HINTS.items() if any((h in lowered) if " " in h else (h in words) for h in hints)]
        return hit[0] if len(hit) == 1 else None

    @cached_property
    def heading_contexts(self) -> dict:
        return {(r['manual_id'], r['number']):(r['title'], r['parent'])
                for r in self.con.execute('SELECT manual_id,number,title,parent FROM units')}

    def _example_context(self, row) -> bool:
        """Use printed headings, including owning sections, rather than expected IDs."""
        title, parent = row['title'], row['parent']
        visited = set()
        while True:
            if EXAMPLE_HEADING.search(title):
                return True
            key = (row['manual_id'], parent)
            if not parent or key in visited or key not in self.heading_contexts:
                return False
            visited.add(key)
            title, parent = self.heading_contexts[key]

    @staticmethod
    def _title_words(text: str) -> tuple[str, ...]:
        # Punctuation/possessives differ across callers and PDF typography.
        text = re.sub(r"['’]s\b", '', text.lower())
        return tuple(w for w in re.findall(r'[a-z0-9]+', text) if w not in STOPWORDS)

    def search(self, query: str, domain: str | None = None, manual_id: str | None = None, kind: str | None = None, limit: int = 8) -> dict:
        limit = max(1, min(limit, 25))
        if kind is not None and kind not in SEARCH_KINDS:
            raise InvalidArgument("invalid_kind", f"unknown kind {kind!r}", suggestions=list(SEARCH_KINDS),
                                  recovery="Use one of the suggested kinds, or omit kind to search all of them.")
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
            hint = self.hinted_domain(query) if domain is None and manual_id is None else None
            title_words = self._title_words(query)
            design_intent = bool(DESIGN_INTENT.search(query)) and not EXAMPLE_HEADING.search(query)

            def rank(row):
                score = row['score'] * (DOMAIN_BOOST if row['domain'] == hint else 1.0)
                if design_intent and self._example_context(row):
                    score *= 0.55
                exact_title = bool(title_words) and title_words == self._title_words(row['title'])
                return (not exact_title, score)

            rows = sorted(rows, key=rank)
            for row in rows:
                if row["unit_id"] in seen or (not row["text"] and not row["table_markdown"] and not row["image_count"] and not self.transcriptions(row["id"])):
                    continue
                seen.add(row["unit_id"])
                hit = self._unit_dict(row, full=False)
                hit["match"] = "text"
                hit["snippet"] = self._snippet(row, row["snip"])
                results.append(hit)
                if len(results) >= limit:
                    break
        results = results[:limit]
        return {"query": query, "results": results, "coverage": self.coverage(query, domain, manual_id, len(results)),
                "attribution": attribution()}

    def coverage(self, query: str, domain: str | None, manual_id: str | None, found: int) -> dict:
        """What was searched, and whether the question asks for a manual that is not indexed."""
        indexed_domains = sorted({m["domain"] for m in self.manuals.values()})
        searched = [mid for mid, m in self.manuals.items()
                    if (domain is None or m["domain"] == domain) and (manual_id is None or mid == manual_id)]
        out: dict = {"searched_manuals": searched, "indexed_domains": indexed_domains}

        def describe(ms) -> str:
            return "; ".join(f"{u.title} ({u.year})" for u in ms)

        def set_status(status: str, message: str, ms=()) -> dict:
            out.update(status=status, message=message)
            if ms:
                out["not_indexed"] = [{"id": u.id, "domain": u.domain, "title": u.title, "year": u.year, "status": u.status} for u in ms]
            return out

        if manual_id is not None and manual_id not in self.manuals:
            ms = [u for u in UNINDEXED if manual_id.upper().startswith(u.id)]
            if ms:
                return set_status("manual_not_indexed", f"{describe(ms)} is not indexed, so nothing was searched. "
                                  "Do not answer from other manuals as if they were this one.", ms)
            return set_status("unknown_manual", f"no manual {manual_id!r}; indexed manuals: {', '.join(self.manuals)}.")
        if domain is not None and domain not in indexed_domains:
            ms = [u for u in UNINDEXED if u.domain == domain]
            if ms:
                return set_status("domain_not_indexed", f"No {domain} manual is indexed: {describe(ms)} is not yet available, "
                                  "so nothing was searched. Do not cite other manuals as its requirements.", ms)
            return set_status("unknown_domain", f"unknown domain {domain!r}; indexed domains: {', '.join(indexed_domains)}.")
        text = " " + re.sub(r"[^a-z0-9]+", " ", query.lower().replace("stormwater", "storm water")).strip() + " "
        named = [u for u in UNINDEXED if any(f" {n} " in text for n in u.names)]
        if named:
            return set_status("requested_manual_not_indexed", f"The question names {describe(named)}, which is not indexed. "
                              "Any results come from other manuals and do not establish that manual's requirements; "
                              "say that the manual is unavailable rather than citing them as its provisions.", named)
        topical = [u for u in UNINDEXED if u.domain not in indexed_domains and any(f" {t} " in text for t in u.topics)]
        if topical:
            return set_status("topic_may_be_outside_corpus", f"This topic is mainly covered by {describe(topical)}, which is not "
                              "indexed. Use the results only if they address the question directly.", topical)
        if not found:
            return set_status("no_match", f"No passages matched in {', '.join(searched)}. The indexed manuals may not cover this question.")
        return set_status("ok", "Results come from the searched manuals.")

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

        if c.get("verified_text"):
            parts += ["[VERIFIED TRANSCRIPTION: checked against the printed page; takes precedence over extracted text for what it covers]",
                      c["verified_text"], ""]
        if c.get("unverified_regions"):
            parts.append("Unverified source region. " + " ".join(c.get("transcription_notes",[])))
        if c.get("table_markdown"):
            parts.append(c["table_markdown"])
            if c.get("needs_review"):
                parts.append("\nNote: this table's layout could not be read with confidence. "
                             "Confirm values against the printed page before use.")
        parts += picture_lines(c)
        if c.get("text"):
            label = "[EXTRACTED TEXT: PDF text layer, not visually verified"
            if c.get("reading_text"):
                label += "; known defects and possible omissions are marked inline in square brackets"
            parts += [label + "]", c.get("reading_text") or c["text"]]
        for t in c.get("tables", []):
            parts += ["", f"{t['citation']}"]
            if t.get("verified_text"):
                parts.append(t["verified_text"])
            parts += [t["table_markdown"]] if t.get("table_markdown") else picture_lines(t)
        if c.get("equations"):
            parts += ["", "[EQUATIONS in this clause: a verified equation takes precedence over the same expression in the extracted text; unverified ones are marked]"]
        for e in c.get("equations", []):
            parts += ["", e["citation"], e.get("verified_text", "Unverified equation region. " + " ".join(e.get("transcription_notes",[]))), *picture_lines(e)]
        meta = {k: c[k] for k in ("kind", "number", "page_label", "pdf_page", "citation", "citation_plain", "source_name", "source_icon") if c.get(k) is not None}
        meta["manual"] = c["manual"]["id"]
        if c.get("unverified_regions"):
            meta["unverified_regions"] = c["unverified_regions"]
        if c.get("verified_transcriptions"):
            meta["verified_transcriptions"] = c["verified_transcriptions"]
        if c.get("equations"):
            meta["equations"] = c["equations"]
        if c.get("needs_review"):
            meta["needs_review"] = True
        if c.get("text_quality"):
            meta["text_quality"] = c["text_quality"]
        if c.get("evidence_precedence"):
            meta["evidence_precedence"] = c["evidence_precedence"]
        if c.get("images"):
            meta["images"] = c["images"]
        return {"id": c["id"], "title": f"{SOURCE_NAME} · {c['citation_plain']}", "text": "\n".join(parts).strip(), "url": c.get("url"), "metadata": meta}
