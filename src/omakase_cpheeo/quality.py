"""Signals about the extracted text layer: known defects and likely omissions.

Extracted text is never edited. These functions describe where it is unreliable so a
reader can be pointed at the verified transcription or the printed page instead.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

DEFECTS = Path(__file__).resolve().parents[2] / "data" / "text-defects.json"

ORDINALS = ("firstly", "secondly", "thirdly", "fourthly", "fifthly", "sixthly", "seventhly", "eighthly")
_ORDINAL = re.compile(r"\b(" + "|".join(ORDINALS) + r")\b", re.I)
# "(a) ", "a) " at a line start, or "(f) " inside a line: list items a-h.
_LETTER = re.compile(r"(?:^[ \t]*\(?|\()([a-h])\)\s", re.M)


@dataclass(frozen=True)
class Gap:
    kind: str  # ordinal | letter
    missing: tuple[str, ...]
    offset: int  # position in the text of the first item after the gap

    def to_dict(self) -> dict:
        what = "ordinal list" if self.kind == "ordinal" else "lettered list"
        shown = ", ".join(self.missing if self.kind == "ordinal" else (f"({m})" for m in self.missing))
        return {"kind": "possible_omission", "missing": list(self.missing),
                "note": f"The extracted {what} skips {shown}; text may be missing. Read the printed page before relying on this passage."}


def _gaps(found: list[tuple[int, int, str]], labels, kind: str) -> list[Gap]:
    """found: (index in sequence, text offset, label) for each item, in text order."""
    first: dict[int, int] = {}
    for i, off, _ in found:
        first.setdefault(i, off)
    if len(first) < 2:  # a single item is not a list
        return []
    out, present = [], sorted(first)
    for prev, nxt in zip(present, present[1:]):
        if nxt - prev > 1:
            out.append(Gap(kind, tuple(labels(i) for i in range(prev + 1, nxt)), first[nxt]))
    # A list that starts late ("Secondly ... Thirdly") lost its opening items.
    if kind == "ordinal" and present[0] > 0:
        out.insert(0, Gap(kind, tuple(labels(i) for i in range(present[0])), first[present[0]]))
    return out


def enumeration_gaps(text: str) -> list[Gap]:
    """Skipped items in "Firstly ... Thirdly" or "(a) ... (d)" lists: a sign of lost lines.

    Lettered lists that start after (a) are not reported; they often continue a list
    begun in the previous clause.
    """
    if not text:
        return []
    ords = [(ORDINALS.index(m.group(1).lower()), m.start(), m.group(1)) for m in _ORDINAL.finditer(text)]
    letters = [(ord(m.group(1)) - 97, m.start(), m.group(1)) for m in _LETTER.finditer(text)]
    gaps = _gaps(ords, lambda i: ORDINALS[i].capitalize(), "ordinal")
    gaps += _gaps(letters, lambda i: chr(97 + i), "letter")
    return sorted(gaps, key=lambda g: g.offset)


class TextDefects:
    """Curated, source-checked defects in extracted text (data/text-defects.json).

    Each entry names the exact extracted span, what the printed page reads, and the
    verified transcription that shows it.
    """

    def __init__(self, path: Path = DEFECTS):
        self.path = path

    @cached_property
    def by_unit(self) -> dict[str, list[dict]]:
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text())
        if data.get("schema_version") != 1:
            raise ValueError(f"unsupported text-defects schema in {self.path}")
        out: dict[str, list[dict]] = {}
        for d in data["defects"]:
            missing = {"unit_id", "extracted", "reading", "note"} - d.keys()
            if missing:
                raise ValueError(f"text defect missing {sorted(missing)}: {d}")
            out.setdefault(d["unit_id"], []).append(d)
        return out

    def for_unit(self, unit_id: str, text: str) -> list[dict]:
        """Defects for a unit, each marked with whether its span is found in the current text."""
        out = []
        for d in self.by_unit.get(unit_id, []):
            entry = {k: d[k] for k in ("extracted", "reading", "verified_id", "note") if d.get(k)}
            entry["located"] = d["extracted"] in (text or "")
            out.append(entry)
        return out


def annotate(text: str, defects: list[dict], gaps: list[Gap]) -> str:
    """The extracted text with defects and possible omissions marked inline."""
    inserts: list[tuple[int, int, str]] = []  # (start, end, replacement)
    for d in defects:
        start = text.find(d["extracted"]) if d.get("located") else -1
        if start < 0:
            continue
        see = f"; see {d['verified_id']}" if d.get("verified_id") else ""
        inserts.append((start, start + len(d["extracted"]),
                        f"{d['extracted']} [extraction defect: the printed page reads \"{d['reading']}\"{see}]"))
    for g in gaps:
        shown = ", ".join(g.missing if g.kind == "ordinal" else (f"({m})" for m in g.missing))
        inserts.append((g.offset, g.offset, f"[possible omission: {shown} missing from the extracted text; read the printed page] "))
    out, pos = [], 0
    for start, end, rep in sorted(inserts, key=lambda x: (x[0], x[1])):
        if start < pos:  # overlapping marks: keep the first
            continue
        out += [text[pos:start], rep]
        pos = end
    out.append(text[pos:])
    return "".join(out)
