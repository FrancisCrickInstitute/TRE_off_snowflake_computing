import boto3
import json
import urllib.parse

from os import environ
from shared.utils import template_to_yaml, apply
from shared.email_client import notification

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
lambda_client = boto3.client('lambda')


@notification(secrets_manager=secrets_manager, function_name="setup experiment")
def handler(event, context):
    """
    Lambda function that creates new experiment in collaboration account.

    Based on input from ServiceNow, it generates template 12_new_experiments,
    and using flows, applies the template in Snowflake account.

    For the experiment, new warehouses, schemas and resource monitors are created,
    and permissions on these resources are granted to relevant roles.

    Args:
        event(dict): event triggered by put to s3, containing reference to a json input from ServiceNow, similar to:
                    {
                        "NAME_OF_BODY": "COLLABORATION",
                        "NAME_OF_EXPERIMENT": "TEST_EXPERIMENT",
                        "CREDITS_COLLAB_EXPERIMENTER": "10",
                        "CONTRACT_PERIOD": "MONTHLY",
                        "START_TIMESTAMP": "2222-05-11",
                        "END_TIMESTAMP": "2222-09-23",
                        "NOTIFY_PERCENT": "95",
                        "CREDITS_COLLAB_DATA_CURATOR": "5"
                    }

    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # get json input
    file = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)

    template = "12_new_experiments"
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

    sf_account = "{}-{}".format(org_name, json_input["NAME_OF_BODY"]).lower()

    if 'Revert' in event and event['Revert']:
        apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account, revert=True)
    else:
        apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account)

    if 'Test' in event and event['Test']:
        return

    lambda_client.invoke(FunctionName=f'{environ["project"]}_update_svn_experiment_records_{environ["env"]}',
                         InvocationType='Event')
