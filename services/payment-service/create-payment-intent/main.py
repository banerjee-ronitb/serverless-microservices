import stripe
from aws_lambda_powertools import Logger, Tracer, Metrics
import boto3
import os
from botocore.exceptions import ClientError

stripe.api_key = os.environ.get("STRIPE_API_KEY")

logger = Logger(service="create_payment_intent")
tracer = Tracer(service="create_payment_intent")
metrics = Metrics(namespace="create_payment_intent")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("AccountTable")


class PaymentIntentCreationException(Exception):
    def __int__(self, metadata):
        self.metadata = metadata


def add_item(client_secret, order_id):
    try:
        item = {
            "orderId": order_id,
            "paymentIntentId": client_secret,
            "status": "payment_intent.created"
        }
        response = table.put_item(Item=item, ReturnConsumedCapacity="TOTAL")
        logger.info("DDB Operation", details={
            "type": "put_item",
            "tableName": "AccountTable",
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits")
        })
        return response
    except ClientError as err:
        raise PaymentIntentCreationException(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        order_id = event.get("orderId")
        order_value = event.get("orderValue")
        if not order_value:
            raise ValueError("Invalid Request")
        output = stripe.PaymentIntent.create(
            amount=order_value,
            currency="inr",
            automatic_payment_methods={"enabled": True}
        )
        add_item(output.client_secret, order_id)
        logger.info("Successfully generated Payment Intent", details={
            "orderId": order_id
        })
        return {"secret": output.client_secret}
    except PaymentIntentCreationException:
        logger.error("Payment Intent creation failed for order id" + order_id)
        raise
