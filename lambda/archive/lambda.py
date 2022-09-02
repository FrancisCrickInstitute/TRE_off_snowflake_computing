import boto3
import json
import urllib.parse

from os import environ
from shared.utils import template_to_yaml, apply, generate_password
from shared.email_client import notification
import snowflake.connector

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
lambda_client = boto3.client('lambda')
events = boto3.client('events')

@notification(secrets_manager=secrets_manager, function_name="archive")
def handler(event, context):
    """
    Lambda function that creates archive for collaboration/entity account.

    Based on input from ServiceNow, it generates template 14_archive_objects,
    and using flows, applies the template in Snowflake account.

    For the experiment, new warehouses, schemas and resource monitors are created,
    and permissions on these resources are granted to relevant roles.

    Args:
        event(dict): event triggered by put to s3, containing reference to a json input from ServiceNow, similar to:
                    {
                      
                    }

    """

    commands = [
        'use role ACCOUNTADMIN;',
        'SHOW TRANSACTIONS IN ACCOUNT;']

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # get json input
    file = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)
    password = secrets_manager.get_secret_value(
        SecretId=json_input["NAME_OF_BODY"]
    )['SecretString']
    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']
    sf_account = "{}-{}".format(org_name, json_input["NAME_OF_BODY"]).lower()
    ctx = snowflake.connector.connect(
            user='ACCOUNTADMIN_MAIN',
            password=password,
            account=sf_account
        )
    cs = ctx.cursor()
    for command in commands:
        cs.execute(command)
    table = cs.fetchall()
    cs.close()
    ctx.close()
    if len(table) != 0:
        # If we still have queries running. Schedule event to re-run archive in 1 day
        schedule_archive(event)

    template = "14_archive_objects"

    template_to_yaml(json_input, template)

    sf_account = "{}-{}".format(org_name, json_input["NAME_OF_BODY"]).lower()

    apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account)
    delete_scheduler(event)
    if 'Test' in event and event['Test']:
        return

def schedule_archive(event):
    """
    Creates scheduled event that triggers archiev lambda function the next 24 hours.
    Scheduled event is deleted after archive process succeeds.
    Args:
        event(dict): event that is passed as argument to archive.
    """
    # TO-DO: email to accountable person about query are running
    name = "archive_{}".format(generate_password(15))
    rule = events.put_rule(
        Name=name,
        ScheduleExpression="rate(1 day)",
        State="ENABLED",
    )

    arn = lambda_client.get_function(
        FunctionName=f'{environ["project"]}_setup_account_{environ["env"]}'
    )['Configuration']['FunctionArn']

    event['name'] = name
    event['fn_arn'] = arn

    lambda_client.add_permission(
        FunctionName=arn,
        StatementId=name,
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=rule["RuleArn"]
    )
    events.put_targets(
        Rule=name,
        Targets=[
            {
                "Id": name,
                "Arn": arn,
                "Input": json.dumps(event)
            }
        ]
    )

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

handler(None, None)