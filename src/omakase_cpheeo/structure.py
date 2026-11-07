"""Split a manual into citable units: numbered sections, tables, and figure captions.

A unit's id is its citation handle, e.g. "SEW-2013-A:3.5" (section) or
"SEW-2013-A:T3.2" (table). Ids are derived from the manual's own numbering, so
they stay stable across re-ingestion.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import pymupdf

from .corpus import Manual
from .extract import Line, Page, is_image_only, read_page
from .texttables import TextTable, find_text_tables, rows_markdown

SECTION = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,6})\.?(?:\s+(.*))?$")
CHAPTER = re.compile(r"^CHAPTER\s+(\d+)\s*[:.-]?\s*(.*)$", re.I)
APPENDIX = re.compile(r"^APPENDIX\s+(A\s*[\d.]+[-\d.]*)\s*(.*)$", re.I)
ANNEXURE = re.compile(r"^Annexure\s+(\d+\.\d+)\s*[:.-]\s*(\S.*)$", re.I)
LEADER_DOTS = re.compile(r"\.{5,}|…{2,}")  # table-of-contents leader dots
# Captions start with a capitalised title; "Table 3.7 gives the analysis..." is prose.
TABLE_CAPTION = re.compile(r"^Table\s+(\d+[.-]\d+[A-Za-z]?)(?:\s*[:.-]\s*|\s+)([A-Z(\d].*)$")
FIGURE_CAPTION = re.compile(r"^Fig(?:ure|\.)\s*(\d+[.-]\d+[A-Za-z]?)(?:\s*[:.-]\s*|\s+)([A-Z(\d].*)$")
# "Table 1.1: Title" with a colon is a caption even when not bold; prose never has the colon.
COLON_CAPTION = re.compile(r"^(?:Table|Fig(?:ure|\.))\s*\d+(?:[.-]\d+)?[A-Za-z]?\s*:")
# Inside an annexure, tables and figures are numbered from 1 again: "Table 4: Node Data".
ANNEX_TABLE_CAPTION = re.compile(r"^Table\s+(\d+)\s*[:.-]\s+([A-Z(\d].*)$")
ANNEX_FIGURE_CAPTION = re.compile(r"^Fig(?:ure|\.)\s*(\d+)\s*[:.-]\s+([A-Z(\d].*)$")
TABLE_REF = re.compile(r"\bTables?\s+(\d+[.-]\d+[A-Za-z]?)")
MAX_HEADING_X = 110.0
TABLE_IMAGE_DPI = int(os.environ.get("OMAKASE_CPHEEO_TABLE_IMAGE_DPI", "200"))
FIGURE_IMAGE_DPI = int(os.environ.get("OMAKASE_CPHEEO_FIGURE_IMAGE_DPI", "130"))


@dataclass
class Unit:
    id: str
    manual_id: str
    kind: str  # chapter | section | table | figure | appendix | annexure
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
    table_source: str = ""  # "image" (a picture in the PDF) | "text" (text in the PDF)
    images: list[dict] = field(default_factory=list)  # crops of the printed page, see render_crop
    needs_review: bool = False
    review_notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


def _heading(line: Line) -> tuple[str, str, str] | None:
    """Return (kind, number, title) when a line opens a new unit."""
    if not line.bold or LEADER_DOTS.search(line.text):
        return None
    # Chapter and appendix titles are centred; section headings sit at the left margin.
    if m := CHAPTER.match(line.text):
        return ("chapter", m.group(1), m.group(2).strip())
    if m := APPENDIX.match(line.text):
        return ("appendix", re.sub(r"\s+", "", m.group(1)), m.group(2).strip())
    if m := ANNEXURE.match(line.text):
        return ("annexure", m.group(1), m.group(2).strip())
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
    layout = manual.layout
    pages = [read_page(doc[i], layout) for i in range(len(doc)) if i + 1 not in skip]
    text_tables = _TextTables(doc, pages) if layout.tables == "text" else None

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
        if _is_list_page(page):  # a list of annexures or chapters, not the headings themselves
            continue
        claimed_images: set[int] = set()
        owners = [(0.0, current)]
        for li, line in enumerate(page.lines):
            if text_tables and text_tables.claims(idx, line):
                continue  # the line is a cell of a table already read
            if pending_title is not None:
                if line.bold and not _heading(line) and not TABLE_CAPTION.match(line.text):
                    pending_title.title = line.text
                    pending_title = None
                    continue
                pending_title = None

            caption_ok = (line.bold or not layout.bold_captions or bool(COLON_CAPTION.match(line.text))) and not LEADER_DOTS.search(line.text)
            in_annex = chapter == "AN" and current is not None
            if caption_ok and (m := TABLE_CAPTION.match(line.text) or (in_annex and ANNEX_TABLE_CAPTION.match(line.text))):
                number, uid = _dotted(m.group(1)), f"T{_dotted(m.group(1))}"
                if in_annex:  # "Table 4" of Annexure 6.3
                    number, uid = f"{number}, Annexure {current.number}", f"{current.id.split(':', 1)[1]}-T{number}"
                table = add(_new_unit(manual, "table", uid, number, m.group(2), chapter, current, page))
                if text_tables:
                    text_tables.attach(table, idx, line, claimed_images)
                else:
                    _attach_table(table, doc, page, pages[idx + 1] if idx + 1 < len(pages) else None, line, claimed_images)
                continue
            if caption_ok and (m := FIGURE_CAPTION.match(line.text) or (in_annex and ANNEX_FIGURE_CAPTION.match(line.text))):
                number, uid = _dotted(m.group(1)), f"F{_dotted(m.group(1))}"
                if in_annex:
                    number, uid = f"{number}, Annexure {current.number}", f"{current.id.split(':', 1)[1]}-F{number}"
                fig = add(_new_unit(manual, "figure", uid, number, m.group(2), chapter, current, page))
                _attach_figure(fig, doc, page, line, claimed_images)
                continue

            head = _heading(line)
            if head:
                kind, number, title = head
                if kind == "chapter":
                    chapter = number
                elif kind == "appendix":
                    chapter = "A"
                elif kind == "annexure":
                    chapter = "AN"
                uid = {"chapter": f"CH{number}", "annexure": f"AN{number}"}.get(kind, number)
                if kind == "section" and not number.startswith(f"{chapter}.") and chapter:
                    # Numbered lists inside text can look like headings; real headings
                    # always carry the current chapter number.
                    head = None
                else:
                    current = add(_new_unit(manual, kind, uid, number, title, chapter or number.split(".")[0], current, page))
                    owners.append((line.bbox[1], current))
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

        for i, bbox in enumerate(page.images):
            if i in claimed_images:
                continue
            owner = next((u for y, u in reversed(owners) if y <= bbox[1]), None)
            if owner is not None:
                owner.images.append(render_crop(doc, page, bbox, kind="table"))
                owner.page_end = max(owner.page_end, page.number)
                owner.label_end = page.label or owner.label_end

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
        # Tables and figures point at the unit they sit in, by its id suffix ("3.6", "AN6.1").
        parent=current.id.split(":", 1)[1] if current and kind in ("table", "figure") else None,
        page_start=page.number,
        page_end=page.number,
        label_start=page.label,
        label_end=page.label,
    )


def render_crop(doc: pymupdf.Document, page: Page, bbox, *, kind: str) -> dict:
    """A picture of part of a printed page, for an assistant to read directly.

    Tables: grayscale PNG at TABLE_IMAGE_DPI, so small digits stay sharp. Figures and
    whole pages: JPEG at FIGURE_IMAGE_DPI.
    """
    pg = doc[page.number - 1]
    rect = pymupdf.Rect(bbox) & pg.rect if bbox else pg.rect
    pad = 4
    rect = pymupdf.Rect(rect.x0 - pad, rect.y0 - pad, rect.x1 + pad, rect.y1 + pad) & pg.rect
    if kind == "table":
        pix = pg.get_pixmap(dpi=TABLE_IMAGE_DPI, clip=rect, colorspace=pymupdf.csGRAY)
        data, mime = pix.tobytes("png"), "image/png"
    else:
        pix = pg.get_pixmap(dpi=FIGURE_IMAGE_DPI, clip=rect)
        data, mime = pix.tobytes("jpeg", jpg_quality=80), "image/jpeg"
    return {"pdf_page": page.number, "page_label": page.label, "bbox": [round(v, 1) for v in rect],
            "width": pix.width, "height": pix.height, "mime": mime, "data": data}


def _image_below(page: Page, next_page: Page | None, caption: Line, claimed: set[int]):
    """The picture under a table caption: on this page, or at the top of the next."""
    candidates = [(page, i, bb) for i, bb in enumerate(page.images) if bb[1] >= caption.bbox[1] - 5 and i not in claimed]
    if not candidates and next_page is not None:
        candidates = [(next_page, i, bb) for i, bb in enumerate(next_page.images) if bb[1] < 250]
    if not candidates:
        return None
    host, i, bb = min(candidates, key=lambda c: (c[0].number, c[2][1]))
    if host is page:
        claimed.add(i)
    return host, bb


def _attach_table(table: Unit, doc: pymupdf.Document, page: Page, next_page: Page | None, caption: Line, claimed: set[int]) -> None:
    """Attach the table picture under its caption.

    The picture is what assistants read; no OCR is run or stored.
    """
    found = _image_below(page, next_page, caption, claimed)
    if found is None:
        # Preserve the printed layout when no reliable crop can be identified.
        table.images.append(render_crop(doc, page, None, kind="table"))
        table.table_source = "image"
        if next_page is not None and caption.bbox[1] > page.height - 160:
            table.images.append(render_crop(doc, next_page, None, kind="table"))
            table.page_end = next_page.number
            table.label_end = next_page.label
        return
    host, bb = found
    table.images.append(render_crop(doc, host, bb, kind="table"))
    table.table_source = "image"
    table.page_end = max(table.page_end, host.number)
    table.label_end = host.label or table.label_end


def _attach_figure(fig: Unit, doc: pymupdf.Document, page: Page, caption: Line, claimed: set[int]) -> None:
    """Use the printed page so vector drawings, legends and multipart figures stay intact."""
    fig.images.append(render_crop(doc, page, None, kind="figure"))


def _is_list_page(page: Page) -> bool:
    """A contents-style page listing three or more chapters or annexures."""
    hits = sum(1 for l in page.lines if l.bold and (CHAPTER.match(l.text) or ANNEXURE.match(l.text)))
    return hits >= 3


class _TextTables:
    """Ruled text tables, found lazily per page and claimed by the caption above them.

    A table that runs to the bottom of a page continues in the first table at the top
    of the next page when no caption sits above that one.
    """

    TOP_GAP = 90.0  # points below the header band where a continuation may start
    BOTTOM_GAP = 170.0  # a table ending this close to the page bottom may continue

    def __init__(self, doc: pymupdf.Document, pages: list[Page]):
        self.doc, self.pages = doc, pages
        self._found: dict[int, list[TextTable]] = {}
        self._claimed: dict[int, list[tuple[float, float, float, float]]] = {}

    def tables(self, idx: int) -> list[TextTable]:
        if idx not in self._found:
            self._found[idx] = find_text_tables(self.doc[self.pages[idx].number - 1])
        return self._found[idx]

    def claims(self, idx: int, line: Line) -> bool:
        x = (line.bbox[0] + line.bbox[2]) / 2
        y = (line.bbox[1] + line.bbox[3]) / 2
        return any(b[0] - 2 <= x <= b[2] + 2 and b[1] - 2 <= y <= b[3] + 2 for b in self._claimed.get(idx, ()))

    def _claim(self, idx: int, t: TextTable) -> None:
        self._claimed.setdefault(idx, []).append(t.bbox)

    def _free(self, idx: int) -> list[TextTable]:
        return [t for t in self.tables(idx) if t.bbox not in self._claimed.get(idx, ())]

    def attach(self, table: Unit, idx: int, caption: Line, claimed_images: set[int]) -> None:
        page = self.pages[idx]
        below = [t for t in self._free(idx) if t.bbox[1] >= caption.bbox[1] - 5]
        # Stop at the next caption: a table below it belongs to that caption.
        nxt = [l.bbox[1] for l in page.lines if l.bbox[1] > caption.bbox[3] and l.bold and TABLE_CAPTION.match(l.text)]
        if nxt:
            below = [t for t in below if t.bbox[1] < min(nxt)]
        host = idx
        if not below and caption.bbox[1] > page.height - self.BOTTOM_GAP and idx + 1 < len(self.pages):
            host, below = idx + 1, [t for t in self._free(idx + 1) if self._at_top(idx + 1, t)]
        if not below:
            # No ruled text table: the table may be a picture, like the sewerage manual's.
            nxt_page = self.pages[idx + 1] if idx + 1 < len(self.pages) else None
            _attach_table(table, self.doc, page, nxt_page, caption, claimed_images)
            return
        first = below[0]
        self._claim(host, first)
        rows = [list(r) for r in first.rows]
        last_page = host
        # Follow the table across page breaks.
        while first.bbox[3] > self.pages[last_page].height - self.BOTTOM_GAP and last_page + 1 < len(self.pages):
            cont = [t for t in self._free(last_page + 1) if self._at_top(last_page + 1, t)]
            if not cont or abs(cont[0].width - len(rows[0])) > 1:
                break
            first = cont[0]
            last_page += 1
            self._claim(last_page, first)
            extra = first.rows[1:] if first.rows and first.rows[0] == rows[0] else first.rows  # repeated header
            rows.extend(list(r) for r in extra)
        end = self.pages[last_page]
        table.page_end = max(table.page_end, end.number)
        table.label_end = end.label or table.label_end
        table.table_markdown = rows_markdown(rows)
        table.table_cells = [{"row": i, "col": j, "text": c} for i, r in enumerate(rows) for j, c in enumerate(r) if c]
        table.table_source = "text"

    def _at_top(self, idx: int, t: TextTable) -> bool:
        """A table at the top of a page with no caption or heading above it."""
        page = self.pages[idx]
        above = [l for l in page.lines if l.bbox[3] <= t.bbox[1] + 1]
        return t.bbox[1] < 62.0 + self.TOP_GAP and not any(TABLE_CAPTION.match(l.text) or _heading(l) for l in above)


def _reflow(text: str) -> str:
    """Join wrapped lines into paragraphs, keeping list items and short lines on their own."""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        starts_item = bool(re.match(r"^([a-z][).]|\(?[ivx]+\)|\(?\d+\)|\d{1,2}\.|[•▪◦-])\s", line))
        if out and not starts_item and not out[-1].endswith((".", ":", ";")) and len(out[-1]) > 60:
            out[-1] = f"{out[-1]} {line}"
        else:
            out.append(line)
    return "\n".join(out)
