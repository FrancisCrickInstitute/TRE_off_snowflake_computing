from asyncio import run
import boto3

from urllib.parse import quote
from okta.client import Client
from shared.email_client import notification

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="add user to Okta group")
def handler(event, context):
    """Add user to the Okta group corresponding to the Snowflake account.

    This function is triggered only for users with field OKTA_ENABLED=true.

    First, obtain user.id from the user's login, which corresponds to <user's principal ID>@email.ac.uk.
    Then assign user.id into group, corresponding to the Snowflake account.

    For REVERT=true, removes user.id from the group, effectively disabling Okta auth to this app for the user.


    Args:
        event(dict): contains LOGIN for user, ACCOUNT_NAME of Snowflake account, REVERT
    """
    login = event["LOGIN"]
    account_name = event["ACCOUNT_NAME"]
    revert = bool(event["REVERT"])

    run(user_to_okta_group(login, account_name, revert))


async def user_to_okta_group(user_email, account_name, revert=False):
    group_id = secrets_manager.get_secret_value(
        SecretId=f"okta_{account_name.lower()}_group_id"
    )['SecretString']
    okta_token = secrets_manager.get_secret_value(
        SecretId="okta_token"
    )['SecretString']

    okta_url = secrets_manager.get_secret_value(
        SecretId="okta_url"
    )['SecretString']

    okta_client = Client({
        'orgUrl': okta_url,
        'token': okta_token
    })

    login = quote(user_email)
    user, response, error = await okta_client.get_user(login)

    if revert:
        await okta_client.remove_user_from_group(groupId=group_id, userId=user.id)
    else:
        await okta_client.add_user_to_group(groupId=group_id, userId=user.id)

