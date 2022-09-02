import boto3

from shared.email_client import notification
from shared.utils import template_to_yaml, apply

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="setup metadata")
def handler(event, context):
    json_input = event['Records'][0]

    template = '10_alter_metadata'

    # transform files and apply on sf
    template_to_yaml(json_input, template)

    # get password
    password = secrets_manager.get_secret_value(
        SecretId=json_input["NAME_OF_BODY"]
    )['SecretString']
    # get org_name
    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']

    sf_account = "{}-{}".format(org_name, json_input["NAME_OF_BODY"])

    apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account)