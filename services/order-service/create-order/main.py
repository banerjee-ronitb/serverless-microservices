import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
import uuid
from orders.OrderStatus import OrderStatus
import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table('OrderTable')

logger = Logger(service="create-order-service")
metrics = Metrics(namespace='create-order-service')
tracer = Tracer(service="create-order-service")


class OrderCreationException(Exception):
    def __int__(self, message: None, details: None):
        self.message = message or 'Order Creation Failed'
        self.details = details or {}


@tracer.capture_method()
def create_order(order):
    try:
        order_id = str(uuid.uuid4())
        order = {
            "orderId": order_id,
            "userId": order["userId"],
            "orderValue": order["orderValue"],
            "orderStatus": OrderStatus.CREATED.value[0],
            "items": order["items"],
            "createdAt": str(datetime.datetime.now())
        }
        response = orders_table.put_item(Item=order, ReturnConsumedCapacity="TOTAL")
        logger.info("DDB Operation", details={
            "type": "put_item",
            "tableName": "OrdersTable",
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits"),
            "metadata": response.get("ResponseMetadata")
        })
        tracer.put_metadata(order_id, order, "create_order")
        return order
    except ClientError as err:
        raise OrderCreationException(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    user_id = event.get('userId')
    order_value = event.get("orderValue")
    items = event.get("items")

    if not (user_id and order_value and items and len(items) > 0 and len(list(filter(lambda x: not (x.get("productId")
                                                                                                    and x.get(
                "quantity")), items))) == 0):
        raise ValueError('Invalid Request')
    try:
        response = create_order(event)
        logger.info("Order Created Successfully", details=response)
        return response
    except OrderCreationException as err:
        logger.exception(err)
        raise
