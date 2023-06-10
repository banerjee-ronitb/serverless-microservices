from aws_lambda_powertools import Logger, Tracer, Metrics
import boto3
from botocore.exceptions import ClientError

logger = Logger(service="retrieve-catalog-service")
tracer = Tracer(service="retrieve-catalog-service")
metrics = Metrics(namespace="retrieve-catalog-service")

dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
table = dynamodb.Table("CatalogTable")


class CatalogRetrieveException(Exception):
    def __init__(self, message):
        self.message = message or 'Catalog Retrieve Exception'


def scan_items(last_evaluated_key):
    try:
        response = None
        if last_evaluated_key:
            response = table.scan(
                Limit=20,
                ExclusiveStartKey=last_evaluated_key,
                ReturnConsumedCapacity='TOTAL'
            )
        else:
            response = table.scan(
                Limit=20,
                ReturnConsumedCapacity='TOTAL'
            )
        logger.info("DDB Operation", details={
            "metadata": response.get("ResponseMetadata"),
            "type": "scan",
            "tableName":"CatalogTable",
            "consumed-capacity": response.get("ConsumedCapacity").get("CapacityUnits")
        }

        )
        return {
            "Items": response.get('Items'),
            "LastEvaluatedKey": response.get("LastEvaluatedKey")
        }
    except ClientError as err:
        raise CatalogRetrieveException(err)


@tracer.capture_lambda_handler()
@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    try:

        if event.get("LastEvaluatedKey"):
            return scan_items(event.get("LastEvaluatedKey"))
        return scan_items(None)
    except CatalogRetrieveException as err:
        logger.exception(err)
        raise
