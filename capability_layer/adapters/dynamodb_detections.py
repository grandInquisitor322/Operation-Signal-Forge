from __future__ import annotations
from decimal import Decimal
from typing import Any, Optional
from capability_layer.ports import DetectionReadPort

def _from_dynamo(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value

class DynamoDbDetectionReader(DetectionReadPort):
    def __init__(self, table_name, *, dynamodb_resource=None):
        import boto3
        self._table = (dynamodb_resource or boto3.resource("dynamodb")).Table(table_name)

    def get_cell(self, cell_id):
        resp = self._table.get_item(Key={"cell_id": cell_id})
        item = resp.get("Item")
        return _from_dynamo(item) if item else None

    def list_cells(self, *, site_id=None, min_fused_probability=None, limit=20):
        resp = self._table.scan(Limit=max(limit * 3, 50))
        items = [_from_dynamo(i) for i in resp.get("Items", [])]
        out = []
        for cell in items:
            if site_id is not None and cell.get("site_id") != site_id:
                continue
            if min_fused_probability is not None:
                if float(cell.get("fused_probability") or 0) < min_fused_probability:
                    continue
            out.append(cell)
            if len(out) >= limit:
                break
        return out
