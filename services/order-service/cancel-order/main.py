import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from botocore.exceptions import ClientError
from orders.OrderStatus import OrderStatus

dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table("OrderTable")

logger = Logger(service="cancel-order-service")
tracer = Tracer(service="cancel-order-service")
metrics = Metrics(namespace="cancel-order-service")


class OrderCancellationException(Exception):
    def __init__(self, message):
        self.message = message or 'Order Cancellation Exception'


@tracer.capture_method()
def cancel_order(order_id, reason):
    try:
        response = orders_table.update_item(
            Key={"orderId": order_id},
            UpdateExpression="SET #reason = :reason, #orderStatus= :orderStatusCancelled",
            ExpressionAttributeNames={
                "#orderStatus": "orderStatus",
                "#reason": "reason"
            },
            ExpressionAttributeValues={
                ":orderStatusCancelled": OrderStatus.CANCELLED.value[0],
                ":reason": reason
            },
            ReturnValues="ALL_NEW"
        )
        logger.info("DDB Operation", details={
            "type": "update_item",
            "table": "orderTable",
            "metadata": response.get("ResponseMetadata"),
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits")
        })
        return response
    except ClientError as err:
        raise OrderCancellationException(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    order_id = event.get("detail").get("orderId")
    status = event.get("detail").get("status")
    detail_type = event.get("detail-type")
    reason = event.get("detail").get("reason", None)
    if not order_id and status:
        raise ValueError("Invalid Request")

    try:
        if (detail_type == "payment_intent.refund" and status == "succeeded") or detail_type == "payment_intent.failed":
            response = cancel_order(order_id, reason or "Payment Failed")
            logger.info("Order Cancelled", details={
                "orderId": order_id
            })
            return response

        elif detail_type == "payment_intent.refund" and status == "Failure":
            raise OrderCancellationException(message="Failed to cancel order. Payment Refund isn't successful")

    except OrderCancellationException as err:
        logger.exception(err)
        raise
