"""Turn a table that is embedded as an image into rows of cells.

Tesseract cannot read a whole ruled table: the grid lines break its layout analysis.
So the grid is found first, the lines are erased, the cleaned image is OCR'd once,
and each recognised word is assigned to the grid cell that contains it.
"""

from __future__ import annotations

import csv
import re
import io
import os
import subprocess
from dataclasses import dataclass

import cv2
import numpy as np
import pymupdf

RENDER_DPI = int(os.environ.get("OMAKASE_CPHEEO_TABLE_DPI", "300"))
MIN_RULE_PX = 90
LOW_CONFIDENCE = 70.0


@dataclass
class Cell:
    row: int
    col: int
    text: str
    confidence: float  # lowest word confidence in the cell, 0-100
    rowspan: int = 1
    colspan: int = 1
    suspect: bool = False  # breaks its column's number format, e.g. "1120" among "1.124"


@dataclass
class OcrTable:
    rows: list[list[Cell]]
    mode: str  # "grid" when cells came from ruled lines, "lines" for the fallback
    min_confidence: float

    @property
    def suspect_cells(self) -> list[Cell]:
        return [c for r in self.rows for c in r if c.suspect]

    @property
    def needs_review(self) -> bool:
        return self.min_confidence < LOW_CONFIDENCE or self.mode != "grid" or bool(self.suspect_cells)

    def as_markdown(self) -> str:
        if not self.rows:
            return ""
        width = max(c.col + c.colspan for r in self.rows for c in r)
        lines = []
        for i, row in enumerate(self.rows):
            cells = [""] * width
            for c in row:
                cells[c.col] = c.text.replace("|", "/")
            lines.append("| " + " | ".join(cells) + " |")
            if i == 0:
                lines.append("|" + "---|" * width)
        return "\n".join(lines)


def render_region(page: pymupdf.Page, bbox: tuple[float, float, float, float]) -> np.ndarray:
    pix = page.get_pixmap(clip=pymupdf.Rect(bbox), dpi=RENDER_DPI, annots=False, colorspace=pymupdf.csGRAY)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width).copy()


def _line_masks(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    bw = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
    # A rule must be much longer than any glyph stroke. At RENDER_DPI a 10-11 pt capital is
    # about 40 px tall, so anything shorter than MIN_RULE_PX is treated as text.
    h_len = max(MIN_RULE_PX, gray.shape[1] // 20)
    v_len = max(MIN_RULE_PX, gray.shape[0] // 25)
    horiz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1)))
    vert = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len)))
    return horiz, vert


def _cell_boxes(horiz: np.ndarray, vert: np.ndarray) -> list[tuple[int, int, int, int]]:
    # Close small gaps so cell borders form closed boxes.
    grid = cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((3, 3), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(grid), connectivity=4)
    h, w = grid.shape
    boxes = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        touches_edge = x == 0 or y == 0 or x + bw >= w or y + bh >= h
        if touches_edge or bw < 15 or bh < 12 or area < 0.5 * bw * bh:
            continue
        boxes.append((int(x), int(y), int(x + bw), int(y + bh)))
    return boxes


def _ocr_words(gray: np.ndarray) -> list[tuple[int, int, int, int, str, float]]:
    ok, png = cv2.imencode(".png", gray)
    if not ok:
        return []
    proc = subprocess.run(
        ["tesseract", "stdin", "stdout", "--psm", "11", "--dpi", str(RENDER_DPI), "tsv"],
        input=png.tobytes(),
        capture_output=True,
        check=True,
    )
    words = []
    for rec in csv.DictReader(io.StringIO(proc.stdout.decode("utf8", "replace")), delimiter="\t", quoting=csv.QUOTE_NONE):
        text = (rec.get("text") or "").strip()
        if not text or rec.get("conf") in (None, "-1"):
            continue
        x, y, w, h = (int(rec[k]) for k in ("left", "top", "width", "height"))
        words.append((x, y, x + w, y + h, text, float(rec["conf"])))
    return words


def _cluster(values: list[int], tol: int) -> list[int]:
    """Collapse nearby edge positions into one representative each."""
    out: list[int] = []
    for v in sorted(values):
        if not out or v - out[-1] > tol:
            out.append(v)
    return out


def _index(edges: list[int], v: int, tol: int) -> int:
    return min(range(len(edges)), key=lambda i: abs(edges[i] - v)) if edges else 0


def _join_words(words: list[tuple[int, int, int, int, str, float]]) -> str:
    """Order words in reading order: cluster into visual lines, then left to right."""
    if not words:
        return ""
    words = sorted(words, key=lambda w: (w[1] + w[3]) / 2)
    lines: list[list] = [[words[0]]]
    for w in words[1:]:
        last = lines[-1][-1]
        if abs((w[1] + w[3]) / 2 - (last[1] + last[3]) / 2) <= max(8, (last[3] - last[1]) * 0.6):
            lines[-1].append(w)
        else:
            lines.append([w])
    return " ".join(" ".join(x[4] for x in sorted(line, key=lambda w: w[0])) for line in lines)


def ocr_table(gray: np.ndarray) -> OcrTable:
    horiz, vert = _line_masks(gray)
    clean = gray.copy()
    rules = cv2.dilate(cv2.bitwise_or(horiz, vert), np.ones((2, 2), np.uint8))
    clean[rules > 0] = 255
    words = _ocr_words(clean)
    boxes = _cell_boxes(horiz, vert)
    if len(boxes) >= 2:
        tol = 12
        ys = _cluster([b[1] for b in boxes] + [b[3] for b in boxes], tol)
        xs = _cluster([b[0] for b in boxes] + [b[2] for b in boxes], tol)
        assigned: dict[int, list] = {i: [] for i in range(len(boxes))}
        for w in words:
            cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            for i, (x0, y0, x1, y1) in enumerate(boxes):
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    assigned[i].append(w)
                    break
        by_row: dict[int, list[Cell]] = {}
        for i, (x0, y0, x1, y1) in enumerate(boxes):
            r0, r1 = _index(ys, y0, tol), _index(ys, y1, tol)
            c0, c1 = _index(xs, x0, tol), _index(xs, x1, tol)
            ws = assigned[i]
            cell = Cell(
                row=r0,
                col=c0,
                text=_join_words(ws),
                confidence=min((w[5] for w in ws), default=100.0),
                rowspan=max(1, r1 - r0),
                colspan=max(1, c1 - c0),
            )
            by_row.setdefault(r0, []).append(cell)
        rows = [sorted(by_row[r], key=lambda c: c.col) for r in sorted(by_row)]
        rows = [r for r in rows if any(c.text for c in r)]
        _flag_number_format(rows)
        conf = min((c.confidence for r in rows for c in r if c.text), default=0.0)
        return OcrTable(rows=rows, mode="grid", min_confidence=conf)
    # No usable grid (e.g. a table ruled only with horizontal lines): keep visual lines.
    text_lines = _join_words(words)
    cells = [[Cell(row=0, col=0, text=text_lines, confidence=min((w[5] for w in words), default=0.0))]]
    return OcrTable(rows=cells, mode="lines", min_confidence=cells[0][0].confidence)


_DECIMAL = re.compile(r"^\d+\.\d+$")
_BARE_INT = re.compile(r"^\d+$")


def _flag_number_format(rows: list[list[Cell]]) -> None:
    """Mark cells whose digits look like a decimal point was lost.

    When most numbers in a column are decimals, a bare integer there is more likely an
    OCR slip ("1120" for "1.120") than a real value. The cell is flagged, never rewritten.
    """
    columns: dict[int, list[Cell]] = {}
    for row in rows:
        for c in row:
            columns.setdefault(c.col, []).append(c)
    for cells in columns.values():
        numeric = [c for c in cells if _DECIMAL.match(c.text) or _BARE_INT.match(c.text)]
        decimals = [c for c in numeric if _DECIMAL.match(c.text)]
        if len(numeric) >= 3 and len(decimals) >= 0.75 * len(numeric):
            for c in numeric:
                if _BARE_INT.match(c.text):
                    c.suspect = True
        for c in cells:
            # Commas inside a decimal ("0,088") and stray symbols around numbers.
            if re.match(r"^\d+,\d{3}$", c.text) and decimals:
                c.suspect = True
            if re.match(r"^[/|\\]\s*\d", c.text):
                c.suspect = True
