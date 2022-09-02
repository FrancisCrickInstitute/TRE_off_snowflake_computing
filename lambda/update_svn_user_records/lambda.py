import boto3

from shared.email_client import notification
from shared.update_servicenow_records import UpdateRecord

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update user records")
def handler(event, context):
    """Lambda function that send all live users,roles data from Snowflake to Service Now.
    This helps Service Now filter existing users while creating forms
    Lambda function uns a query then format as Json and send to Service Now API.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.commands = [
        'use role ACCOUNTADMIN;',
        'use warehouse CORE_WH;',
        'select * from '
        'ORG_ADMIN_DB.ADMIN_SCH.UPDATE_SVN_USER_RECORDS;'
    ]
    update_record.attributes = [
        "u_consortium_id",
        "role", 
        "user",
        "name_of_body"
    ]
    update_record.endpoint = "x_tfci_snowflake_user_records"

    update_record.execute()
