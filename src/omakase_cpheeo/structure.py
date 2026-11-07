"""Split a manual into citable units: numbered sections, tables, and figure captions.

A unit's id is its citation handle, e.g. "SEW-2013-A:3.5" (section) or
"SEW-2013-A:T3.2" (table). Ids are derived from the manual's own numbering, so
they stay stable across re-ingestion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pymupdf

from .corpus import Manual
from .extract import Line, Page, is_image_only, read_page
from .tables import ocr_table, render_region

SECTION = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,6})\.?(?:\s+(.*))?$")
CHAPTER = re.compile(r"^CHAPTER\s+(\d+)\s*[:.-]?\s*(.*)$", re.I)
APPENDIX = re.compile(r"^APPENDIX\s+(A\s*[\d.]+[-\d.]*)\s*(.*)$", re.I)
# Captions start with a capitalised title; "Table 3.7 gives the analysis..." is prose.
TABLE_CAPTION = re.compile(r"^Table\s+(\d+[.-]\d+[A-Za-z]?)\s*[:.-]?\s+([A-Z(\d].*)$")
FIGURE_CAPTION = re.compile(r"^Fig(?:ure|\.)\s*(\d+[.-]\d+[A-Za-z]?)\s*[:.-]?\s+([A-Z(\d].*)$")
TABLE_REF = re.compile(r"\bTables?\s+(\d+[.-]\d+[A-Za-z]?)")
MAX_HEADING_X = 110.0


@dataclass
class Unit:
    id: str
    manual_id: str
    kind: str  # chapter | section | table | figure | appendix
    number: str
    title: str
    chapter: str
    parent: str | None
    page_start: int
    page_end: int
    label_start: str | None
    label_end: str | None
    text: str = ""
    table_markdown: str = ""
    table_cells: list[dict] = field(default_factory=list)
    needs_review: bool = False
    review_notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


def _heading(line: Line) -> tuple[str, str, str] | None:
    """Return (kind, number, title) when a line opens a new unit."""
    if not line.bold:
        return None
    # Chapter and appendix titles are centred; section headings sit at the left margin.
    if m := CHAPTER.match(line.text):
        return ("chapter", m.group(1), m.group(2).strip())
    if m := APPENDIX.match(line.text):
        return ("appendix", re.sub(r"\s+", "", m.group(1)), m.group(2).strip())
    if line.bbox[0] > MAX_HEADING_X:
        return None
    if m := SECTION.match(line.text):
        number = m.group(1)
        # A bare decimal such as "3.5" with no title is still a heading in these
        # manuals (the title sits on the next bold line), but a long number run is a value.
        if len(line.text) > 160:
            return None
        return ("section", number, (m.group(2) or "").strip())
    return None


def _dotted(number: str) -> str:
    """The manual writes both "Table 3.7" and "Table 3-7"; ids always use the dot."""
    return number.replace("-", ".")


def _parent(number: str) -> str | None:
    parts = number.split(".")
    return ".".join(parts[:-1]) if len(parts) > 2 else parts[0] if len(parts) == 2 else None


def build_units(manual: Manual, doc: pymupdf.Document, progress=None) -> list[Unit]:
    skip = {p for a, b in manual.skip_pages for p in range(a, b + 1)}
    units: dict[str, Unit] = {}
    order: list[str] = []
    current: Unit | None = None
    pending_title: Unit | None = None  # heading whose title is on the following bold line
    chapter = ""
    pages = [read_page(doc[i]) for i in range(len(doc)) if i + 1 not in skip]

    def add(unit: Unit) -> Unit:
        if unit.id in units:  # a continued table or a repeated caption
            existing = units[unit.id]
            existing.page_end = max(existing.page_end, unit.page_end)
            existing.label_end = unit.label_end or existing.label_end
            return existing
        units[unit.id] = unit
        order.append(unit.id)
        return unit

    for idx, page in enumerate(pages):
        if progress:
            progress(page.number, len(doc))
        if is_image_only(page) and not page.images:
            continue
        claimed_images: set[int] = set()
        for li, line in enumerate(page.lines):
            if pending_title is not None:
                if line.bold and not _heading(line) and not TABLE_CAPTION.match(line.text):
                    pending_title.title = line.text
                    pending_title = None
                    continue
                pending_title = None

            if m := TABLE_CAPTION.match(line.text):
                number = _dotted(m.group(1))
                table = add(_new_unit(manual, "table", f"T{number}", number, m.group(2), chapter, current, page))
                _attach_table(table, doc, page, pages[idx + 1] if idx + 1 < len(pages) else None, line, claimed_images)
                continue
            if m := FIGURE_CAPTION.match(line.text):
                number = _dotted(m.group(1))
                add(_new_unit(manual, "figure", f"F{number}", number, m.group(2), chapter, current, page))
                continue

            head = _heading(line)
            if head:
                kind, number, title = head
                if kind == "chapter":
                    chapter = number
                elif kind == "appendix":
                    chapter = "A"
                uid = number if kind != "chapter" else f"CH{number}"
                if kind == "section" and not number.startswith(f"{chapter}.") and chapter:
                    # Numbered lists inside text can look like headings; real headings
                    # always carry the current chapter number.
                    head = None
                else:
                    current = add(_new_unit(manual, kind, uid, number, title, chapter or number.split(".")[0], current, page))
                    if kind == "section":
                        current.parent = _parent(number)
                    if not title:
                        pending_title = current
                    continue
            if current is None:
                continue
            current.text += line.text + "\n"
            current.page_end = max(current.page_end, page.number)
            current.label_end = page.label or current.label_end

    result = [units[i] for i in order]
    for u in result:
        u.text = _reflow(u.text)
        u.references = sorted({f"T{_dotted(r)}" for r in TABLE_REF.findall(u.text)} - {f"T{u.number}"})
    return result


def _new_unit(manual: Manual, kind: str, uid: str, number: str, title: str, chapter: str, current: Unit | None, page: Page) -> Unit:
    return Unit(
        id=f"{manual.id}:{uid}",
        manual_id=manual.id,
        kind=kind,
        number=number,
        title=title.strip(),
        chapter=chapter,
        parent=current.number if current and kind in ("table", "figure") else None,
        page_start=page.number,
        page_end=page.number,
        label_start=page.label,
        label_end=page.label,
    )


def _attach_table(table: Unit, doc: pymupdf.Document, page: Page, next_page: Page | None, caption: Line, claimed: set[int]) -> None:
    """Find the table body below its caption: an image on this page, or at the top of the next."""
    candidates = [(page, i, bb) for i, bb in enumerate(page.images) if bb[1] >= caption.bbox[1] - 5 and i not in claimed]
    if not candidates and next_page is not None:
        candidates = [(next_page, i, bb) for i, bb in enumerate(next_page.images) if bb[1] < 250]
    if not candidates:
        table.review_notes.append("no table image found below the caption; body may be text")
        table.needs_review = True
        return
    host, i, bb = min(candidates, key=lambda c: (c[0].number, c[2][1]))
    if host is page:
        claimed.add(i)
    ocr = ocr_table(render_region(doc[host.number - 1], bb))
    table.page_end = max(table.page_end, host.number)
    table.label_end = host.label or table.label_end
    table.table_markdown = ocr.as_markdown()
    table.table_cells = [
        {"row": c.row, "col": c.col, "rowspan": c.rowspan, "colspan": c.colspan, "text": c.text, "confidence": round(c.confidence), "suspect": c.suspect}
        for r in ocr.rows
        for c in r
    ]
    table.needs_review = ocr.needs_review
    if ocr.mode != "grid":
        table.review_notes.append("no ruled grid detected; cells are approximate")
    if ocr.min_confidence < 70:
        table.review_notes.append(f"lowest OCR word confidence {ocr.min_confidence:.0f}")
    if ocr.suspect_cells:
        table.review_notes.append("cells that may have lost a decimal point: " + ", ".join(c.text for c in ocr.suspect_cells))


def _reflow(text: str) -> str:
    """Join wrapped lines into paragraphs, keeping list items and short lines on their own."""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        starts_item = bool(re.match(r"^([a-z]\)|\(?[ivx]+\)|\(?\d+\)|[•▪◦-])\s", line))
        if out and not starts_item and not out[-1].endswith((".", ":", ";")) and len(out[-1]) > 60:
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return "\n".join(out)
