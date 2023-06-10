from aws_lambda_powertools import Logger, Tracer, Metrics
import boto3
from botocore.exceptions import ClientError
import datetime
import json

logger = Logger(service="update-catalog-service")
tracer = Tracer(service="update-catalog-service")
metrics = Metrics(namespace="update-catalog-service")

client = boto3.resource("dynamodb")
order_table = client.Table("OrderTable")
ddb = boto3.client("dynamodb")
events = boto3.client("events")


class CatalogUpdateException(Exception):
    def __init__(self, metadata):
        self.metadata = metadata


class OrderQueryException(Exception):
    def __int__(self, metadata):
        self.metadata = metadata


class QuantityInDeficitError(Exception):
    def __init__(self, message, details):
        self.message = message
        self.details = details


class CatalogQueryException(Exception):
    def __init__(self, metadata):
        self.metadata = metadata


def update_table(order_list, retrieve_list, order_id):
    try:

        deficit_list = []
        transact_write_items = []
        for item in retrieve_list:
            current_item = next(
                (
                    product
                    for product in order_list
                    if product.get("productId") == item.get("product_id")
                ),
                None,
            )
            if current_item:
                if int(item.get("quantity")) < int(current_item.get("quantity")):
                    deficit_list.append({"productId": item.get("product_id")})
                else:
                    item["quantity"] = int(item.get("quantity")) - int(
                        current_item.get("quantity")
                    )
                    transact_write_items.append(item)
        if len(deficit_list) > 0:
            raise QuantityInDeficitError(
                message="Inventory in Deficit", details={"orderId": order_id, "items": deficit_list}
            )

        response = ddb.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "Item": {
                            key: {"N": str(value)}
                            if key == "quantity"
                            else {"S": value}
                            for key, value in item.items()
                        },
                        "TableName": "CatalogTable",
                    }
                }
                for item in transact_write_items
            ],
            ReturnConsumedCapacity="TOTAL"
        )
        logger.info("DDB Operation", details={
            "type": "transact_write_items",
            "tableName": "CatalogTable",
            "metadata": response.get("ResponseMetadata"),
            "consumed_capacity": response.get("ConsumedCapacity")[0].get("CapacityUnits")
        })

        return response
    except ClientError as err:
        raise CatalogUpdateException(err)
    except AttributeError as err:
        raise CatalogUpdateException(err)


# TBD - Replace direct database query with an API Call with service token.
def get_order_by_order_id(order_id):
    try:
        response = order_table.query(
            KeyConditionExpression="orderId = :orderId",
            ExpressionAttributeValues={":orderId": order_id},
            ReturnConsumedCapacity="TOTAL"
        )
        logger.info("DDB Operation", details={
            "metadata": response.get("ResponseMetadata"),
            "type": "query",
            "tableName": "OrderTable",
            "consumed_capacity": response.get("ConsumedCapacity").get("CapacityUnits")
        })
        return response.get("Items")[0]
    except ClientError as err:
        raise OrderQueryException(err)


def query_table(product_ids):
    try:
        request_items = {
            "CatalogTable": {"Keys": [{"product_id": item} for item in product_ids]}
        }
        response = client.batch_get_item(
            RequestItems=request_items, ReturnConsumedCapacity="TOTAL"
        )
        logger.info(
            "DDB Operation",
            details={
                "metadata": response.get("ResponseMetadata"),
                "type": "batch_get_item",
                "tableName": "CatalogTable",
                "consumed-capacity": response.get("ConsumedCapacity")[0].get(
                    "CapacityUnits"
                ),
            },
        )
        return response.get("Responses").get("CatalogTable")
    except ClientError as err:
        raise CatalogQueryException(err)


def trigger_payment_refund(order_id, payment_reference_id):
    events.put_events(
        Entries=[
            {
                "Time": datetime.datetime.now(),
                "Source": "update-catalog-function",
                "Resources": [],
                "DetailType": "inventory_update.failed",
                "Detail": json.dumps(
                    {
                        "orderId": order_id,
                        "paymentReferenceId": payment_reference_id,
                        "reason": "Inventory out of stock",
                    }
                ),
            }
        ]
    )


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:
        order_id = event.get("detail").get("orderId")
        order_details = get_order_by_order_id(order_id)
        if order_details.get("orderStatus") == 'CREATED':
            payment_reference_id = event.get("detail").get("data").get("object").get("id")
            items = order_details.get("items")
            if not items:
                raise ValueError
            product_ids = []
            if len(items) > 0:
                for item in items:
                    product_ids.append(item.get("productId"))
            retrieve_items = query_table(product_ids)
            update_response = update_table(items, retrieve_items, order_id)

            events.put_events(
                Entries=[
                    {
                        "Time": datetime.datetime.now(),
                        "Source": "update-catalog-function",
                        "Resources": [],
                        "DetailType": "inventory_update.succeeded",
                        "Detail": json.dumps(
                            {
                                "orderId": order_id,
                                "payment_reference_id": payment_reference_id,
                            }
                        ),
                    }
                ]
            )
            logger.info("Updated Inventory Successfully with Eventbridge Notification")
            return (
                {"statusCode": 200}
                if update_response.get("ResponseMetadata").get("HTTPStatusCode") == 200
                else {"statusCode": 400}
            )
        else:
            logger.error("Cannot change order status", details=order_details)
    except ValueError as err:
        logger.exception(err)
        raise
    except CatalogQueryException as err:
        logger.exception(err)
        raise
    except OrderQueryException as err:
        logger.exception(err)
        raise
    except CatalogUpdateException as err:
        logger.exception(err)
        raise
    except QuantityInDeficitError as err:
        print(err)
        logger.exception(err.message)
        trigger_payment_refund(err.details.get("orderId"), event.get("detail").get("data").get("object").get("id"))
        raise
