import boto3

from shared.email_client import notification
from shared.update_snowflake_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update snowflake account table")
def handler(event, context):
    """Lambda function that send all user data from ServiceNow to Snowflake
    This helps metadata has more info for reporting like active, and not approved user
    Lambda function send request to ServiceNow user API and get JSON data. Then, it parses
    to INSERT SQL query to write this data to Org_admin account table.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.endpoint = "x_tfci_snowflake_user_records"

    update_record.filter = lambda row:{
    'u_consortium_id_value': row.get('u_consortium_id', {'value': ''}).get('value', ''),
    'email_address': row.get('u_login'),
    'firstname': row.get('firstname'),
    'lastname': row.get('lastname'),
    'role': row.get('role'),
    'using_OKTA': row.get('u_okta'),
    'SERVICE_NOW_ID': row.get('sys_id'),
    'active': row.get('active'),
    'name_of_body_value': row.get('name_of_body', {'value': ''}).get('value', ''),
    'name_of_body_link': row.get('name_of_body', {'link': ''}).get('link', ''),
    'sys_created_by': row.get('sys_created_by'),
    'sys_created_on': row.get('sys_created_on'),
    'sys_updated_on': row.get('sys_updated_on'),
    'sys_updated_by': row.get('sys_updated_by'),
    'sys_mod_count': row.get('sys_mod_count'),
    'sys_tags': row.get('sys_tags'),
    'u_consortium_id_link': row.get('u_consortium_id', {'link': ''}).get('link', ''),
    'testfield': row.get('testfield'),
    'account_name': row.get('account_name'),
    'u_user': row.get('u_user')}

    update_record.execute()


handler(None, None)
