import datetime
from aws_lambda_powertools import Logger, Tracer, Metrics
import json
import stripe
import boto3
from botocore.exceptions import ClientError

logger = Logger(service="payment-intent-webhook")
tracer = Tracer(service="payment-intent-webhook")
metrics = Metrics(namespace="payment-intent-webhook")

# TBD - Webhook Signature Verification
stripe.api_key = ""
endpoint_secret = ""

sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("AccountTable")
events = boto3.client("events")


class PaymentIntentWebHookError(Exception):
    def __init__(self, metadata):
        self.metadata = metadata


def update_account_table(order_id, payment_reference_id, status):
    try:
        response = table.update_item(
            Key={"paymentIntentId": payment_reference_id},
            UpdateExpression=
            "SET #status = :paymentStatus,#updatedAt= :updatedAt,#orderId=:orderId",
            ExpressionAttributeNames={
                "#status": "status",
                "#updatedAt": "updatedAt",
                "#orderId": "orderId"

            },
            ReturnValues="ALL_NEW",
            ExpressionAttributeValues={
                ":paymentStatus": status,
                ":updatedAt": str(datetime.datetime.now()),
                ":orderId": order_id
            },
            ReturnConsumedCapacity='TOTAL'
        )
        logger.info("DDB Operation", details={
            "metadata": response.get("ResponseMetadata"),
            "tableName": "AccountsTable",
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits"),
            "type": "update_item"
        })
    except ClientError as err:
        raise PaymentIntentWebHookError(err)


def get_item(payment_intent_id):
    try:
        response = table.get_item(
            Key={
                "paymentIntentId": payment_intent_id
            },
            ReturnConsumedCapacity="TOTAL"
        )
        logger.info("DDB Operation", details={
            "type": "get_item",
            "tableName": "AccountTable",
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits"),
            "metadata": response.get("ResponseMetadata")
        })
        return response.get("Item")
    except ClientError as err:
        raise PaymentIntentWebHookError(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        payload = event.get("body")
        order_id = get_item(payload.get("data", {}).get("object", {}).get("client_secret")).get("orderId")
        update_account_table(order_id, payload.get("data").get("object").get("id"), payload.get("type"))
        response = events.put_events(
            Entries=[
                {
                    "Time": datetime.datetime.now(),
                    "Source": "payment-intent-webhook-function",
                    "Resources": [],
                    "DetailType": payload.get("type"),
                    "Detail": json.dumps({
                        "orderId": order_id,
                        "data": payload.get("data")
                    })

                }
            ]
        )
        logger.info("Stripe webhook triggered successfully with notifications", details=response)
        return {"success": True}
    except ValueError as e:
        logger.exception(e)
        raise
    except stripe.error.SignatureVerificationError as e:
        logger.exception(e)
        raise
    except PaymentIntentWebHookError as err:
        logger.exception(err)
        raise
