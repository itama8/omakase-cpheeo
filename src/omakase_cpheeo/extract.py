"""Page-level extraction: body lines with positions, printed page labels, and images.

Reader annotations in the source copy (highlights, free-text notes) are removed before
anything is read, so a reader's notes never become manual text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from .corpus import INDESIGN, Layout

PAGE_LABEL = re.compile(r"^\s*([A-Z]?\d*\s*-\s*\d+)\s*$")
PAGE_NUMBER = re.compile(r"^\s*(\d{1,4})\s*$")
# On Word pages the body can start inside the usual header band (landscape pages);
# running headers never look like these.
HIGH_HEADING = re.compile(r"^(?:Annexure|Appendix|APPENDIX|Table|Figure)\s+[A-Z]?\s*\d|^\d{1,2}(?:\.\d{1,2})+\s+[A-Z]")
PRIVATE_GLYPH = re.compile("[\uf000-\uf0ff]")
MIN_IMAGE_W, MIN_IMAGE_H = 150.0, 40.0


@dataclass
class Line:
    text: str
    bbox: tuple[float, float, float, float]
    size: float
    bold: bool


@dataclass
class Page:
    number: int  # 1-based physical page
    label: str | None  # printed page label such as "3 - 105" or "36"
    height: float = 842.0
    lines: list[Line] = field(default_factory=list)
    images: list[tuple[float, float, float, float]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)


def open_clean(path: Path) -> pymupdf.Document:
    """Open a PDF in memory with every annotation removed."""
    doc = pymupdf.open(path)
    for page in doc:
        for annot in list(page.annots()):
            page.delete_annot(annot)
    return doc


def _line_text(spans: list[dict]) -> str:
    text = "".join(s["text"] for s in spans).replace("\t", " ")
    text = PRIVATE_GLYPH.sub("•", text)  # Wingdings/Symbol bullets in Word PDFs
    return re.sub(r"\s+", " ", text).strip()


def read_page(page: pymupdf.Page, layout: Layout = INDESIGN) -> Page:
    out = Page(number=page.number + 1, label=None, height=page.rect.height)
    footer: list[str] = []
    rows: list[Line] = []
    for block in page.get_text("dict", sort=True)["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = _line_text(spans)
            y0 = line["bbox"][1]
            if layout.footer_min_y is not None and y0 > layout.footer_min_y:
                footer.append(text)
                continue
            if y0 < layout.header_max_y and not HIGH_HEADING.match(text):
                continue
            rows.append(Line(text, tuple(line["bbox"]), spans[0]["size"], bool(spans[0]["flags"] & 16)))
    out.lines = _merge_same_row(rows)
    if layout.footer_min_y is None and out.lines:
        # The page number is the lowest line, in the bottom part of the page.
        last = max(out.lines, key=lambda l: l.bbox[1])
        if PAGE_NUMBER.match(last.text) and last.bbox[1] > out.height * 0.85:
            out.lines.remove(last)
            footer.append(last.text)
    for t in footer:
        if layout.label == "number":
            if m := PAGE_NUMBER.match(t):
                out.label = m.group(1)
        elif m := PAGE_LABEL.match(t):
            out.label = re.sub(r"\s*-\s*", " - ", m.group(1).strip())
    if out.label is None and layout.label == "chapter-page":
        # Some appendix sheets are printed sideways: their footer is on the right edge.
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = _line_text(line["spans"])
                if (line["bbox"][0] > page.rect.width * 0.85 or line["bbox"][1] > out.height * 0.85) and (m := PAGE_LABEL.match(text)):
                    out.label = re.sub(r"\s*-\s*", " - ", m.group(1).strip())
    for info in page.get_image_info():
        x0, y0, x1, y1 = info["bbox"]
        if x1 - x0 >= MIN_IMAGE_W and y1 - y0 >= MIN_IMAGE_H:
            out.images.append((x0, y0, x1, y1))
    return out


def _merge_same_row(lines: list[Line]) -> list[Line]:
    """Join fragments on one visual row, e.g. a heading number and its title."""
    merged: list[Line] = []
    for line in sorted(lines, key=lambda l: (round(l.bbox[1]), l.bbox[0])):
        prev = merged[-1] if merged else None
        if prev and abs(prev.bbox[1] - line.bbox[1]) < 2.0 and line.bbox[0] >= prev.bbox[2] - 1:
            prev.text = f"{prev.text} {line.text}"
            prev.bbox = (prev.bbox[0], min(prev.bbox[1], line.bbox[1]), line.bbox[2], max(prev.bbox[3], line.bbox[3]))
            continue
        merged.append(Line(line.text, line.bbox, line.size, line.bold))
    return merged


def is_image_only(page: Page) -> bool:
    return len(re.sub(r"\s", "", page.text)) < 100
