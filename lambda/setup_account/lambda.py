import boto3
import json
import urllib.parse

from os import environ
from shared.utils import template_to_yaml, apply
from shared.email_client import notification

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
lambda_client = boto3.client('lambda')
events = boto3.client('events')


@notification(secrets_manager=secrets_manager, function_name="setup account")
def handler(event, context):
    """
    Lambda function that setups an account in Snowflake.

    Our flow supports 4 types of accounts - collaboration, lab, stp and external account.

    For type collaboration, template 06_collaboration_subaccount is generated from ServiceNow input.
    For types lab, stp and external, template 04_entity_subaccount is generated.

    Using flows, template is applied to a Snowflake account, and all require resources are generated
    - resource monitors
    - databases
    - schemas in databases
    - warehouses
    - roles
    - grants
    - metadata shares

    After successful setup, scheduled event that triggered this lambda function is deleted,
    and three other lambdas are invoked - setup_metadata, update_svn_account_records, create_okta_integration.

    Args:
        event(dict): dictionary obtained from scheduled event, containing reference to a json input from ServiceNow
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

    # get json input
    file = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)

    account_type = json_input["TYPE"].upper()

    # check account type
    if account_type in ["STP", "EXTERNAL", "LAB"]:
        template = "04_entity_subaccount"
    elif account_type == "COLLABORATION":
        template = "06_collaboration_subaccount"
    else:
        raise Exception("Unsupported type of account! Only STP, EXTERNAL, LAB and COLLABORATION types are supported.")

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

    json_input_ACCOUNTADMINBACKUP = {
        "ACTION": "ADD_USER",
        "NAME_OF_BODY": json_input["NAME_OF_BODY"].upper(),
        "CONSORTIUM_ID": json_input["CONSORTIUM_ID"].upper(),
        "ROLE_NAME": "ACCOUNTADMIN",
        "EMAIL": "default@email.ac.uk",
        "OKTA_ENABLED": "false",
        "LOGIN": "ACCOUNTADMIN_BACKUP",
        "REGION": json_input["REGION"].upper(),
        "CHANGE_PASSWORD": "false"
    }

    s3_file = boto3.resource("s3").Object(f'{environ["project"]}-setup-user-{environ["env"]}',
                       f'ACCOUNTADMINBACKUP_{json_input["NAME_OF_BODY"]}.json')

    s3_file.put(Body=json.dumps(json_input_ACCOUNTADMINBACKUP))

    lambda_client.invoke(FunctionName=f'{environ["project"]}_setup_metadata_{environ["env"]}',
                         InvocationType='Event',
                         Payload=json.dumps(event))

    lambda_client.invoke(FunctionName=f'{environ["project"]}_update_svn_account_records_{environ["env"]}',
                         InvocationType='Event')

    if account_type != "EXTERNAL":
        lambda_client.invoke(FunctionName=f'{environ["project"]}_setup_okta_integration_{environ["env"]}',
                             InvocationType='Event',
                             Payload=json.dumps({"ACCOUNT_NAME": json_input["NAME_OF_BODY"]}))

    delete_scheduler(event)


def delete_scheduler(event):
    name = event['name']
    events.remove_targets(
        Rule=name,
        Ids=[
            name,
        ]
    )
    events.delete_rule(
        Name=name
    )
    lambda_client.remove_permission(
        FunctionName=event['fn_arn'],
        StatementId=name
    )
