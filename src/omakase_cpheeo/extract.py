"""Page-level extraction: body lines with positions, printed page labels, and images.

Reader annotations in the source copy (highlights, free-text notes) are removed before
anything is read, so a reader's notes never become manual text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# Running header and footer bands on an A4 page (points). Body text sits between them.
HEADER_MAX_Y = 62.0
FOOTER_MIN_Y = 770.0
PAGE_LABEL = re.compile(r"^\s*([A-Z]?\d*\s*-\s*\d+)\s*$")
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
    label: str | None  # printed page label such as "3 - 105"
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
    return re.sub(r"\s+", " ", text).strip()


def read_page(page: pymupdf.Page) -> Page:
    out = Page(number=page.number + 1, label=None)
    footer: list[str] = []
    rows: list[Line] = []
    for block in page.get_text("dict", sort=True)["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = _line_text(spans)
            y0 = line["bbox"][1]
            if y0 > FOOTER_MIN_Y:
                footer.append(text)
                continue
            if y0 < HEADER_MAX_Y:
                continue
            rows.append(Line(text, tuple(line["bbox"]), spans[0]["size"], bool(spans[0]["flags"] & 16)))
    out.lines = _merge_same_row(rows)
    for t in footer:
        m = PAGE_LABEL.match(t)
        if m:
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
