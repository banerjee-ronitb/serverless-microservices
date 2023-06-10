import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from orders.OrderStatus import OrderStatus
from botocore.exceptions import ClientError
import datetime

dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table("OrderTable")

logger = Logger(service="confirm-order-service")
tracer = Tracer(service="confirm-order-service")
metrics = Metrics(namespace="confirm-order-service")


class OrderConfirmationException(Exception):
    def __init__(self, message: None, details: None):
        self.message = message or 'Order Confirmation Exception'
        self.details = details or {}


@tracer.capture_method()
def confirm_order(order_id, payment_reference_id):
    try:
        response = orders_table.update_item(
            Key={"orderId": order_id},
            UpdateExpression=
            "SET #paymentReferenceId = :paymentReferenceId,#orderStatus= :orderStatusConfirmed,#updatedAt= :updatedAt",
            ExpressionAttributeNames={
                "#paymentReferenceId": "paymentReferenceId",
                "#orderStatus": "orderStatus",
                "#updatedAt": "updatedAt"
            },
            ReturnValues="ALL_NEW",
            ExpressionAttributeValues={
                ":orderStatusConfirmed": OrderStatus.CONFIRMED.value[0],
                ":paymentReferenceId": payment_reference_id,
                ":updatedAt": str(datetime.datetime.now())
            },
            ReturnConsumedCapacity='TOTAL'
        )
        logger.info("DDB Operation", details={
            "type": "update_item",
            "tableName": "OrderTable",
            "metadata": response.get("ResponseMetadata"),
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits")
        })
        return response.get("Attributes")
    except ClientError as err:
        raise OrderConfirmationException(err, {})


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    order_id = event.get("detail").get("orderId");
    payment_reference_id = event.get("detail").get("paymentReferenceId")
    if not order_id and payment_reference_id:
        raise ValueError("Invalid Request")

    try:
        response = confirm_order(order_id, payment_reference_id)
        logger.info("Order Confirmed", details={
            "orderId": order_id,
            "paymentReferenceId": payment_reference_id
        })
        return response;
    except OrderConfirmationException as err:
        logger.exception(err)
        raise
