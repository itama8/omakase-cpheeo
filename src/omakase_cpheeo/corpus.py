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

    @property
    def citation_title(self) -> str:
        return f"CPHEEO {self.title} ({self.edition}, {self.year}), {self.part}"


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
)


def sources_dir() -> Path:
    return Path(os.environ.get("OMAKASE_CPHEEO_SOURCES", DEFAULT_SOURCES))


def manual_by_id(manual_id: str) -> Manual:
    for m in MANUALS:
        if m.id == manual_id:
            return m
    raise KeyError(manual_id)
