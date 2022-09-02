import boto3
import json
import urllib.parse

from shared.utils import template_to_yaml, apply
from shared.email_client import EmailClient, notification

s3_client = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
events = boto3.client('events')
lambda_client = boto3.client('lambda')
email_client = EmailClient(secrets_manager)


@notification(secrets_manager=secrets_manager, function_name="create external stage")
def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # get json input
    file = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)

    # transform files and apply on sf
    template = "15_external_stage"
    template_to_yaml(json_input, template)

    account_name = json_input["NAME_OF_BODY"]

    # credentials for ORG ADMIN ACCOUNT
    password = secrets_manager.get_secret_value(
        SecretId=account_name
    )['SecretString']
    # get org_name
    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']

    sf_account = "{}-{}".format(org_name, account_name).lower()

    # flows apply
    apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account)

    ##############
    # SEND EMAIL #
    ##############
    recipients = ["admin@email.ac.uk"]
    subject = f"External stage in account {account_name} created"

    body = f'External stage {json_input["NAME"]} in {sf_account}.snowflakecomputing.com was successfully created.'

    email_client.send(recipients=recipients, subject=subject, body=body)
