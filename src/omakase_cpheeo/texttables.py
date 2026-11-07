"""Read tables that are real text with ruled lines (Word-generated manuals).

PyMuPDF finds the ruled grid; each cell's text is then read with a clip of the page,
which keeps the PDF's own word spacing. Merged cells come back as None and are left
empty; columns that only hold a "1 2 3 4" column-number row are dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

MIN_ROWS, MIN_COLS = 2, 2


@dataclass
class TextTable:
    bbox: tuple[float, float, float, float]
    rows: list[list[str]]

    @property
    def width(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    def as_markdown(self) -> str:
        return rows_markdown(self.rows)


def rows_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    lines = []
    for i, row in enumerate(rows):
        cells = [c.replace("|", "/") for c in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)


def _cell_text(page: pymupdf.Page, rect) -> str:
    text = page.get_text("text", clip=pymupdf.Rect(rect))
    return re.sub(r"\s+", " ", text).strip()


def _is_number_row(row: list[str]) -> bool:
    """A row of column numbers: "1", "2", "3", ... and blanks."""
    vals = [c for c in row if c]
    return len(vals) >= 2 and vals == [str(i) for i in range(1, len(vals) + 1)]


def _clean(grid: list[list[str | None]]) -> list[list[str]]:
    rows = [[c or "" for c in r] for r in grid]
    rows = [r for r in rows if not _is_number_row(r)]
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [j for j in range(width) if any(r[j] for r in rows)]
    rows = [[r[j] for j in keep] for r in rows]
    return [r for r in rows if any(r)]


def find_text_tables(page: pymupdf.Page) -> list[TextTable]:
    """Ruled tables on a page, top to bottom, with cell text."""
    if not page.get_drawings():
        return []
    out = []
    for tb in page.find_tables().tables:
        grid = [[None if c is None else _cell_text(page, c) for c in row.cells] for row in tb.rows]
        rows = _clean(grid)
        if len(rows) >= MIN_ROWS and max((len(r) for r in rows), default=0) >= MIN_COLS:
            out.append(TextTable(tuple(tb.bbox), rows))
    return sorted(out, key=lambda t: t.bbox[1])
