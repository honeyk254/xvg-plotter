"""XVG parser (SPEC §5). Never raises on malformed input; collects warnings."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from .models import Dataset, ParseStats, SeriesSpec, XvgFile

_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\S+')
_KNOWN_KINDS = ("xy", "xydy", "xydx", "xydxdy")


def _unquote(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return re.sub(r"\\(.)", r"\1", tok[1:-1])
    return tok


def _text(toks: list[str]) -> str:
    return " ".join(_unquote(t) for t in toks)


class _Parser:
    def __init__(self) -> None:
        self.f = None  # XvgFile under construction
        self._rows: list[list[float]] = []
        self._ncols: int | None = None
        self._kinds: dict[int, str] = {}
        self._legends: dict[int, str] = {}
        self._bad = 0
        self._ragged = 0

    def parse(self, path: Path) -> XvgFile:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")  # BOM-tolerant
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        self.f = XvgFile(path=path)
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            c = s[0]
            if c == "#":
                continue
            if c == "@":
                self._directive(s[1:])
            elif c == "&":
                self._flush()
            else:
                self._data(s)
        self._flush()
        if self.f.stats.rows_ok == 0:
            self.f.warnings.append("no data rows")
        if self._bad:
            self.f.warnings.append(f"{self._bad} data row(s) skipped: unparseable tokens")
        if self._ragged:
            self.f.warnings.append(f"{self._ragged} data row(s) skipped: wrong column count")
        return self.f

    # -- directives --------------------------------------------------------

    def _directive(self, rest: str) -> None:
        toks = _TOKEN.findall(rest)
        if not toks:
            return
        head = toks[0]
        if head == "title" and len(toks) > 1:
            self.f.title = _text(toks[1:])
        elif head == "subtitle" and len(toks) > 1:
            self.f.subtitle = _text(toks[1:])
        elif head in ("xaxis", "yaxis") and len(toks) > 2 and toks[1] == "label":
            if head == "xaxis":
                self.f.x_label = _text(toks[2:])
            else:
                self.f.y_label = _text(toks[2:])
        elif re.fullmatch(r"s\d+", head) and len(toks) > 1:
            idx = int(head[1:])
            key, val = toks[1], toks[2:]
            if key == "legend" and val:
                self._legends[idx] = _text(val)
            elif key == "type" and val and val[0] in _KNOWN_KINDS:
                self._kinds[idx] = val[0]
            else:
                self.f.stats.directives_ignored += 1  # color/symbol/linetype/...
        else:
            self.f.stats.directives_ignored += 1  # world/with/target/gN/...

    # -- data rows ---------------------------------------------------------

    def _data(self, line: str) -> None:
        vals = []
        for tok in line.split():
            try:
                vals.append(float(tok))  # accepts nan/inf/1.0e5
            except ValueError:
                self._bad += 1
                self.f.stats.rows_skipped += 1
                return
        if self._ncols is None:
            self._ncols = len(vals)
        elif len(vals) != self._ncols:
            self._ragged += 1
            self.f.stats.rows_skipped += 1
            return
        self._rows.append(vals)
        self.f.stats.rows_ok += 1

    # -- dataset assembly --------------------------------------------------

    def _flush(self) -> None:
        f = self.f
        ncols = self._ncols or 0
        if ncols:
            if self._rows:
                arr = np.asarray(self._rows, dtype=float)
                columns = [arr[:, i].copy() for i in range(ncols)]
            else:
                columns = [np.empty(0) for _ in range(ncols)]
            series = self._build_series(ncols)
            f.datasets.append(Dataset(index=len(f.datasets), columns=columns, series=series))
            f.stats.n_cols = ncols
        self._rows, self._ncols, self._kinds, self._legends = [], None, {}, {}

    def _build_series(self, ncols: int) -> list[SeriesSpec]:
        """Consume columns after X per '@ sN type' directives; leftovers become
        independent line series (the gmx energy layout, SPEC §5.4)."""
        specs: list[SeriesSpec] = []
        col, s = 1, 0
        while col < ncols:
            kind = self._kinds.get(s, "xy")
            leg = self._legends.get(s)
            if kind == "xy":
                specs.append(SeriesSpec(col, leg)); col += 1
            elif kind == "xydy" and col + 1 < ncols:
                specs.append(SeriesSpec(col, leg, "xydy", dy_col=col + 1)); col += 2
            elif kind == "xydx" and col + 1 < ncols:
                specs.append(SeriesSpec(col + 1, leg, "xydx", dx_col=col)); col += 2
            elif kind == "xydxdy" and col + 2 < ncols:
                specs.append(SeriesSpec(col + 1, leg, "xydxdy", dx_col=col, dy_col=col + 2)); col += 3
            else:
                self.f.warnings.append(
                    f"series s{s}: type '{kind}' needs more columns than the file has; drawn as line")
                specs.append(SeriesSpec(col, leg)); col += 1
            s += 1
        return specs


def parse_file(path: Path | str) -> XvgFile:
    return _Parser().parse(Path(path))
