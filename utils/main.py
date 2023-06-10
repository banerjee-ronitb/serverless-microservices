import boto3
import json

client = boto3.client("dynamodb")
s3_obj = boto3.client('s3')


def lambda_handler(event, context):
    s3_client_obj = s3_obj.get_object(Bucket='rb-23-04-23-bucket', Key='data.json')
    s3_client_data = s3_client_obj['Body'].read().decode('utf-8')

    response = client.transact_write_items(
        TransactItems=json.loads(s3_client_data),
        ReturnConsumedCapacity="TOTAL"
    )
    print(response)
    return response
