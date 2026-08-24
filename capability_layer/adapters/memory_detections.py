from __future__ import annotations
from typing import Any, Optional
from capability_layer.ports import DetectionReadPort

class InMemoryDetectionReader(DetectionReadPort):
    def __init__(self, cells=None):
        self._by_id = {}
        for cell in cells or []:
            if cell.get("cell_id"):
                self._by_id[str(cell["cell_id"])] = dict(cell)

    def seed(self, cell):
        self._by_id[str(cell["cell_id"])] = dict(cell)

    def get_cell(self, cell_id):
        found = self._by_id.get(cell_id)
        return dict(found) if found else None

    def list_cells(self, *, site_id=None, min_fused_probability=None, limit=20):
        out = []
        for cell in self._by_id.values():
            if site_id is not None and cell.get("site_id") != site_id:
                continue
            if min_fused_probability is not None:
                if float(cell.get("fused_probability") or 0) < min_fused_probability:
                    continue
            out.append(dict(cell))
            if len(out) >= limit:
                break
        return out
