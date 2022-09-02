import json
import urllib.parse
from os import environ

import boto3

from shared.email_client import notification, EmailClient
from shared.utils import template_to_yaml, apply, generate_password

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="setup user")
def handler(event, context):
    """
    Performs action on user in the Snowflake account.
    4 types of action are supported:
        1. ADD_USER: creates new user and assign him role
        2. DELETE_USER: deletes existing user
        3. ADD_ROLE: add new role to an existing user
        4. REMOVE_ROLE: remove role from an existing user

    Based on action type, generates template 08_new_users or 09_new_role, and using ``flows``,
    applies the template on Snowflake account.

    Generates password for the user, and send him the password VIA email.
    User needs to reset the password at the first login, unless Okta authentication is enabled for the user.

    If the Okta auth is enabled and action type is ADD_USER, lambda function ``setup_okta_user`` is triggered.

    Args:
        event(dict): event triggered by put to s3, containing reference to a json input from ServiceNow, similar to
                    {
                      "ACTION": "ADD_USER",
                      "NAME_OF_BODY": "COLLABORATION",
                      "LASTNAME": "",
                      "FIRSTNAME": "",
                      "CONSORTIUM_ID": "CON0001015",
                      "ROLE_NAME": "ROLE_BOARD_MEMBER",
                      "EMAIL": "",
                      "OKTA_ENABLED": "false",
                      "LOGIN": "",
                      "REGION": "AWS_EU_WEST_2"
                    }
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    # get json input
    file = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    json_input = json.loads(file)

    action = json_input["ACTION"].lower()
    if "add_user" == action:
        revert = False
        template = "08_new_users"
    elif "delete_user" == action:
        revert = True
        template = "08_new_users"
    elif "add_role" == action:
        revert = False
        template = "09_new_role"
    elif "remove_role" == action:
        revert = True
        template = "09_new_role"
    else:
        print("Incorrect input! Json must contain ACTION: add_user, delete_user, add_role or remove_role")
        return

    okta_enabled = json_input["OKTA_ENABLED"].upper() == "TRUE"
    user_password = generate_password(10)

    # transform files and apply on sf
    template_to_yaml(json_input, template, user_password)

    name_of_body = json_input["NAME_OF_BODY"]
    # get password
    password = secrets_manager.get_secret_value(
        SecretId=name_of_body
    )['SecretString']
    # get org_name
    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']

    sf_account = "{}-{}".format(org_name, name_of_body).lower()

    apply(template, sf_username="ACCOUNTADMIN_MAIN", sf_password=password, sf_account=sf_account, revert=revert)

    # real time org admin replica refresh
    if json_input.get("REGION") != "AWS_EU_WEST_2":
        template = "13_org_admin_refresh"
        admin_account = "{}-{}".format(org_name, "org_admin").lower()
        password = secrets_manager.get_secret_value(
            SecretId="ACCOUNTADMIN_MAIN"
        )['SecretString']

        template_to_yaml(json_input, template)
        apply(template, sf_account=admin_account, sf_username="ACCOUNTADMIN_MAIN", sf_password=password)

    if 'Test' in event and event['Test']:
        return

    ##############
    # SEND EMAIL #
    ##############
    recipient = json_input["EMAIL"]
    login = json_input["LOGIN"]
    role = json_input["ROLE_NAME"]

    if action == "delete_user":
        subject = "Snowflake user deleted"
        body = f'User {login} successfully removed from Snowflake account https://{sf_account}.snowflakecomputing.com'
    elif action == "add_user" and okta_enabled:
        subject = "Snowflake user created"
        body = f'''
        User name: {login}<br>
        Account: https://{sf_account}.snowflakecomputing.com.<br>
        Use Okta to login - selecting the correct names snowflake app.<br>
        Password for programmatic access will be sent in the following email.'''
    elif action == "add_user":
        subject = "Snowflake user created"
        body = f'''
        User name: {login} <br>
        Account: https://{sf_account}.snowflakecomputing.com.<br>
        Password will be sent in the following email.'''
    elif action == "remove_role":
        subject = "Role removed for Snowflake user"
        body = f'Role {role} removed for user {login} in Snowflake account https://{sf_account}.snowflakecomputing.com'
    else:
        subject = "Role added to Snowflake user"
        body = f'Role {role} added for user {login} in Snowflake account https://{sf_account}.snowflakecomputing.com'

    EmailClient(secrets_manager).send_with_footnote(recipient=recipient, subject=subject, body=body)

    if action == "add_user":
        EmailClient(secrets_manager).send_with_footnote(recipient=recipient, subject=subject, body=user_password)

    lambda_client.invoke(FunctionName=f'{environ["project"]}_update_svn_user_records_{environ["env"]}',
                         InvocationType='Event')

    if okta_enabled:
        lambda_client.invoke(FunctionName=f'{environ["project"]}_setup_okta_user_{environ["env"]}',
                             InvocationType='Event',
                             Payload=json.dumps({"LOGIN": login,
                                                 "ACCOUNT_NAME": name_of_body,
                                                 "REVERT": revert}))
