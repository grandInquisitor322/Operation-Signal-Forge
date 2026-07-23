"""
DLQ Replay Function for Signal Forge
====================================
Manually replay messages from the Dead Letter Queue back to the main SQS queue.
"""

import json
import os
import boto3

sqs = boto3.client('sqs')

DLQ_URL = os.environ['DLQ_URL']
MAIN_QUEUE_URL = os.environ['MAIN_QUEUE_URL']


def handler(event, context):
    """
    Triggered manually (e.g. via CLI or EventBridge schedule).
    Reads up to 10 messages from DLQ and re-sends them to the main queue.
    """
    replayed = 0
    failed = 0

    try:
        response = sqs.receive_message(
            QueueUrl=DLQ_URL,
            MaxNumberOfMessages=10,
            VisibilityTimeout=60,
            WaitTimeSeconds=10
        )

        messages = response.get('Messages', [])

        for msg in messages:
            try:
                # Re-send to main queue
                sqs.send_message(
                    QueueUrl=MAIN_QUEUE_URL,
                    MessageBody=msg['Body']
                )

                # Delete from DLQ
                sqs.delete_message(
                    QueueUrl=DLQ_URL,
                    ReceiptHandle=msg['ReceiptHandle']
                )

                replayed += 1
                print(f"✅ Replayed message ID: {msg['MessageId']}")

            except Exception as e:
                print(f"❌ Failed to replay message: {str(e)}")
                failed += 1

        return {
            "statusCode": 200,
            "replayed": replayed,
            "failed": failed,
            "message": f"Replayed {replayed} messages from DLQ"
        }

    except Exception as e:
        print(f"Critical error in DLQ replay: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e)
        }