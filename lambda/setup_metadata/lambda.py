import boto3
import json
import urllib.parse

from shared.utils import template_to_yaml, apply, add_locator
from shared.email_client import notification
import os

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="setup metadata")
def handler(event, context):
    """Lambda function that build metadata tables in Snowflake.

    Based on json input from ServiceNow, this lambda function generates template 10_metadata 
    and 11_org_admin_acknowledge.
    Template 10_metadata creates tables and stored procedures in subaccount, template 11_org_admin_acknowledge
    create share/replica database from subaccount and update the views.
    
    Args:
        event(dict): event sent by set_up account lambda function, containing reference to a json input from ServiceNow
                     {
                      "END_TIMESTAMP": "",
                      "CONSORTIUM_ID": "CON0001018",
                      "CREDITS_BUDGET_COLLABORATION": "110",
                      "CONTRACT_PERIOD": "MONTHLY",
                      "NAME_OF_BODY": "DARE_UK_TRE",
                      "NOTIFY_PERCENT": "90",
                      "START_TIMESTAMP": "2022-07-14",
                      "TYPE": "COLLABORATION",
                      "REGION": "AWS_EU_WEST_2"
                    }
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    # derive account type

    # get json input
    file = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)
    json_input['ENV'] = os.environ['env']

    template = "10_metadata"

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

    if 'Revert' in event and event['Revert']:
        apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account, revert=True)
    else:
        apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account)

    json_input = add_locator(json_input=json_input, user="ACCOUNTADMIN_MAIN", password=password, account=sf_account)

    # Org admin part
    template = "11_org_admin_acknowledge"
    admin_account = "{}-{}".format(org_name, "org_admin")
    admin_username = "ACCOUNTADMIN_MAIN"
    admin_password = secrets_manager.get_secret_value(
        SecretId="ACCOUNTADMIN_MAIN"
    )['SecretString']

    template_to_yaml(json_input, template)

    if 'Revert' in event and event['Revert']:
        pass
        apply(template, sf_username=admin_username, sf_password=admin_password, sf_account=admin_account, revert=True)
    else:
        apply(template, sf_username=admin_username, sf_password=admin_password, sf_account=admin_account)

