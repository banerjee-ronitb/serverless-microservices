import os

from aws_lambda_powertools import Logger, Tracer, Metrics
import boto3
from botocore.exceptions import ClientError
import datetime
import stripe
import json

logger = Logger(service="refund-payment-service")
tracer = Tracer(service="refund-payment-service")
metrics = Metrics(namespace="refund-payment-service")

dynamodb = boto3.resource("dynamodb")
accounts_table = dynamodb.Table("AccountTable")
events = boto3.client("events")

stripe.api_key = os.environ.get("STRIPE_API_KEY")


class RefundPaymentException(Exception):
    def __init__(self, metadata):
        self.metadata = metadata


def update_account_table(order_id, payment_reference_id, reason, refund_id):
    try:
        response = accounts_table.update_item(
            Key={"paymentIntentId": payment_reference_id},
            UpdateExpression=
            "SET #status = :paymentStatus,#updatedAt= :updatedAt,#reason= :reason,#refundId=:refundId,#orderId=:orderId",
            ExpressionAttributeNames={
                "#status": "status",
                "#updatedAt": "updatedAt",
                "#reason": "reason",
                "#refundId": "refundId",
                "#orderId": "orderId"
            },
            ReturnValues="ALL_NEW",
            ExpressionAttributeValues={
                ":paymentStatus": "payment_intent.refund",
                ":updatedAt": str(datetime.datetime.now()),
                ":reason": reason,
                ":refundId": refund_id,
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
        raise RefundPaymentException(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        order_id = event.get("detail").get("orderId")
        payment_reference_id = event.get("detail").get("paymentReferenceId")
        reason = event.get("detail").get("reason")
        response = stripe.Refund.create(payment_intent=payment_reference_id)

        update_account_table(order_id, payment_reference_id, reason, response.get("id"))
        notification = events.put_events(
            Entries=[
                {
                    "Time": datetime.datetime.now(),
                    "Source": "refund-payment-function",
                    "Resources": [],
                    "DetailType": "payment_intent.refund",
                    "Detail": json.dumps({
                        "orderId": order_id,
                        "status": response.get("status"),
                        "reason": reason
                    })

                }
            ]
        )
        logger.info("Payment Refund attempted.", details=notification)
    except RefundPaymentException as err:
        logger.exception(err)
        raise
