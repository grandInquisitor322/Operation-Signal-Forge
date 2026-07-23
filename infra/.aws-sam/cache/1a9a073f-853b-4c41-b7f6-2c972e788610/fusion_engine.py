"""
Operational Signal Forge - Sensor Fusion Engine
==================================================
Lambda function that processes sensor readings from SQS.
"""

import json
import os
import time
import boto3
import traceback

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ.get("DETECTIONS_TABLE")
ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN")
HIGH_CONFIDENCE_THRESHOLD = float(os.environ.get("HIGH_CONFIDENCE_THRESHOLD", "0.75"))

table = dynamodb.Table(TABLE_NAME)


def process_reading(payload: dict) -> dict:
    """
    Process a single sensor reading and save/update the cell in DynamoDB
    """
    try:
        print(f"DEBUG: Received payload: {json.dumps(payload, default=str)}")
        
        site_id = payload.get('site_id', 'unknown')
        cell_id = f"{site_id}-{int(time.time())}"   # Simple unique cell for now
        
        item = {
            'cell_id': cell_id,
            'site_id': site_id,
            'sensor_id': payload.get('sensor_id'),
            'sensor_type': payload.get('sensor_type'),
            'timestamp': payload.get('timestamp', int(time.time())),
            'lat': payload.get('lat'),
            'lon': payload.get('lon'),
            'reading': payload.get('reading', {}),
            'last_updated': int(time.time()),
            'status': 'detected'
        }
        
        print("DEBUG: Full cell structure being saved:")
        print(json.dumps(item, indent=2, default=str))
        
        # Save to DynamoDB
        response = table.put_item(Item=item)
        
        print(f"✅ Successfully saved detection → cell_id: {cell_id}")
        return {"alert": False, "cell_id": cell_id}
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in process_reading: {str(e)}")
        print(traceback.format_exc())
        raise


def handler(event, context):
    """
    SQS Trigger Handler
    """
    results = []
    
    for record in event.get("Records", []):
        try:
            payload = json.loads(record["body"])
            result = process_reading(payload)
            results.append(result)
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            print(f"Raw record: {record}")
            raise  # Let SQS retry → DLQ

    return {
        "processed": len(results),
        "alerts_fired": sum(1 for r in results if r.get("alert"))
    }