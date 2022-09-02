import boto3
import json
import urllib.parse

from os import environ
from shared.utils import template_to_yaml, apply, generate_password
from shared.email_client import EmailClient, notification

s3_client = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
events = boto3.client('events')
lambda_client = boto3.client('lambda')


@notification(secrets_manager=secrets_manager, function_name="create account")
def handler(event, context):
    """Lambda function that creates new account in Snowflake.

    Based on json input from ServiceNow, this lambda function generates template 03_setup_account, and using flows,
    creates new account in Snowflake organization account based on 03_setup_account template.

    Password for user ACCOUNTADMIN_MAIN is generated, saved to AWS secrets and sent to admin email.

    Provisioning the URL for new account can take several minutes,
    hence new lambda function `setup-account` is scheduled and periodically triggered, until it succeeds.

    Args:
        event(dict): event triggered by put to s3, containing reference to a json input from ServiceNow
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
    file = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)

    account_password = generate_password(12)

    # transform files and apply on sf
    account = "03_setup_subaccount"
    json_input = template_to_yaml(json_input, account, account_password)

    # credentials for ORG ADMIN ACCOUNT
    admin_username = "ACCOUNTADMIN_MAIN"
    admin_password = secrets_manager.get_secret_value(
        SecretId="ACCOUNTADMIN_MAIN"
    )['SecretString']
    admin_account = secrets_manager.get_secret_value(
        SecretId="ORGADMIN_ACCOUNT"
    )['SecretString']
    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']

    sf_account = "{}-{}".format(org_name, admin_account)

    if 'SkipCreate' not in json_input or json_input['SkipCreate'].upper() == "FALSE":
        # flows apply
        apply(template=account, sf_account=sf_account, sf_username=admin_username, sf_password=admin_password)

        # save password for newly created account
        secrets_manager.create_secret(
            Name=json_input["NAME_OF_BODY"],
            SecretString=account_password
        )

    ##############
    # SEND EMAIL #
    ##############
    recipients = ["default@email.ac.uk"]
    subject = "Snowflake account created"

    body = """
        Account {}-{}.snowflakecomputing.com was successfully created.
        Password for user ACCOUNTADMIN_MAIN is {}""".format(org_name, json_input["NAME_OF_BODY"], account_password)

    EmailClient(secrets_manager).send(recipients=recipients, subject=subject, body=body)

    schedule_setup(event)


def schedule_setup(event):
    """
    Creates scheduled event that triggers setup-account lambda function every 10 minutes.
    Scheduled event is deleted after setup-account succeeds.
    Args:
        event(dict): event that is passed as argument to setup-account.
    """
    name = "setup_account_{}".format(generate_password(15))
    rule = events.put_rule(
        Name=name,
        ScheduleExpression="rate(10 minutes)",
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
