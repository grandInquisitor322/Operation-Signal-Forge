"""
Operational Signal Forge - Dashboard API
==========================================
API Gateway -> Lambda (proxy integration). Serves detection cell data to the
dashboard: list by site, by bounding box, and detail/status update for a cell.

Routes (via API Gateway HTTP API):
  GET  /sites/{site_id}/cells          -> all cells for a site
  GET  /sites/{site_id}/cells?min_score=0.5
  POST /cells/{cell_id}/status         -> { "status": "searching"|"cleared"|"confirmed" }
"""

import json
import os
import time
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("DETECTIONS_TABLE", "signal-forge-detections")
table = dynamodb.Table(TABLE_NAME)

SITE_INDEX = "site-index"


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "")
    qs = event.get("queryStringParameters") or {}
    params = event.get("pathParameters") or {}

    try:
        if method == "GET" and "cells" in path and "site_id" in params:
            return list_cells_for_site(params["site_id"], qs)
        if method == "POST" and "status" in path and "cell_id" in params:
            body = json.loads(event.get("body") or "{}")
            return update_cell_status(params["cell_id"], body)
        return respond(404, {"error": "not found"})
    except Exception as e:
        return respond(500, {"error": str(e)})


def list_cells_for_site(site_id, qs):
    min_score = float(qs.get("min_score", 0))

    resp = table.query(
        IndexName=SITE_INDEX,
        KeyConditionExpression=Key("site_id").eq(site_id),
        FilterExpression=Attr("fused_probability").gte(Decimal(str(min_score))),
    )
    items = resp.get("Items", [])

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            IndexName=SITE_INDEX,
            KeyConditionExpression=Key("site_id").eq(site_id),
            FilterExpression=Attr("fused_probability").gte(Decimal(str(min_score))),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    return respond(200, {"site_id": site_id, "count": len(items), "cells": items})


def update_cell_status(cell_id, body):
    new_status = body.get("status")
    if new_status not in ("unassigned", "searching", "cleared", "confirmed"):
        return respond(400, {"error": "invalid status"})

    update_expr_parts = ["#s = :s", "updated_at = :u"]
    expr_names = {"#s": "status"}
    expr_values = {":s": new_status, ":u": int(time.time())}

    if "notes" in body:
        update_expr_parts.append("notes = :notes")
        expr_values[":notes"] = str(body["notes"])[:2000]

    if "survivors_estimate" in body:
        try:
            count = int(body["survivors_estimate"])
            if count < 0 or count > 50:
                return respond(400, {"error": "survivors_estimate out of range"})
            update_expr_parts.append("survivors_estimate = :sv")
            expr_values[":sv"] = count
        except (ValueError, TypeError):
            return respond(400, {"error": "survivors_estimate must be an integer"})

    if "confirmed_by" in body:
        update_expr_parts.append("confirmed_by = :cb")
        expr_values[":cb"] = str(body["confirmed_by"])[:200]

    if new_status == "confirmed" and "confirmed_by" not in body:
        return respond(400, {
            "error": "confirmed status requires confirmed_by"
        })

    table.update_item(
        Key={"cell_id": cell_id},
        UpdateExpression="SET " + ", ".join(update_expr_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return respond(200, {"cell_id": cell_id, "status": new_status})


def respond(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=decimal_default),
    }