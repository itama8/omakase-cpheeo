"""The fixed set of manuals the service indexes.

Each entry names one PDF and the citation metadata every result carries. Source PDFs
live outside the repo; set OMAKASE_CPHEEO_SOURCES to the folder that holds them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCES = Path.home() / "Downloads" / "CPHEEO"


@dataclass(frozen=True)
class Layout:
    """How a manual's pages are laid out; the parser reads these instead of guessing."""

    header_max_y: float = 62.0  # running header lines sit above this (points)
    # Fixed footer band (InDesign manuals). None: the footer is only the page number,
    # read from the lowest line on the page (Word manuals, where its height varies).
    footer_min_y: float | None = 770.0
    label: str = "chapter-page"  # "3 - 105" | "number" (a plain running page number)
    tables: str = "image"  # image: OCR the picture under a caption | text: ruled text tables
    bold_captions: bool = False  # only bold "Table 2.2: ..." lines are captions


INDESIGN = Layout()
WORD = Layout(footer_min_y=None, label="number", tables="text", bold_captions=True)


@dataclass(frozen=True)
class Manual:
    id: str  # stable citation prefix, e.g. "SEW-2013-A"
    domain: str  # water | sewerage | stormwater | solid-waste
    title: str
    part: str
    edition: str
    year: int
    file: str  # path relative to the sources folder
    # Physical PDF pages to skip (1-based, inclusive), e.g. image-only front matter.
    skip_pages: tuple[tuple[int, int], ...] = ()
    layout: Layout = INDESIGN

    @property
    def citation_title(self) -> str:
        return f"CPHEEO {self.title} ({self.edition}, {self.year}), {self.part}"


# Cover subtitle "(Drink from Tap)" left out so citations do not nest parentheses.
_WS = "Manual on Water Supply and Treatment Systems"
_WS_DIR = "Water Supply_2023"

MANUALS: tuple[Manual, ...] = (
    Manual(
        id="SEW-2013-A",
        domain="sewerage",
        title="Manual on Sewerage and Sewage Treatment Systems",
        part="Part A: Engineering",
        # The 2013 text calls the 1993 manual the "2nd edition"; the image-only cover
        # was not OCR-checked for the exact wording.
        edition="Third edition",
        year=2013,
        file="Seweage CPHEEO.pdf",
        skip_pages=((1, 86),),
    ),
    Manual(
        id="WS-2024-A",
        domain="water",
        title=_WS,
        part="Part A: Engineering - Planning, Design and Implementation",
        edition="Fourth edition",
        year=2024,
        file=f"{_WS_DIR}/Part-A-Manual-Engineering-Planning-Design-and-Implementation(3).pdf",
        skip_pages=((1, 85),),
        layout=WORD,
    ),
    Manual(
        id="WS-2024-B",
        domain="water",
        title=_WS,
        part="Part B: Operation and Maintenance",
        edition="Fourth edition",
        year=2024,
        file=f"{_WS_DIR}/Part-B-Manual-Operation-and-Maintenance(5).pdf",
        skip_pages=((1, 67),),
        layout=WORD,
    ),
    Manual(
        id="WS-2024-C",
        domain="water",
        title=_WS,
        part="Part C: Management",
        edition="Fourth edition",
        year=2024,
        file=f"{_WS_DIR}/Part-C-Manual-Management(4).pdf",
        skip_pages=((1, 52),),
        layout=WORD,
    ),
)


def sources_dir() -> Path:
    return Path(os.environ.get("OMAKASE_CPHEEO_SOURCES", DEFAULT_SOURCES))


def manual_by_id(manual_id: str) -> Manual:
    for m in MANUALS:
        if m.id == manual_id:
            return m
    raise KeyError(manual_id)
