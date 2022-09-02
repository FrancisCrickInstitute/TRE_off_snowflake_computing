import boto3

from shared.email_client import notification
from shared.update_snowflake_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update snowflake account table")
def handler(event, context):
    """Lambda function that send all accounts data from Snowflake to Service Now.
    This helps Service Now has more data of accounts such as account locator, Url,
    created on. 
    Lambda function uns a query then format as Json and send to Service Now API.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.endpoint = "x_tfci_snowflake_account_records"

    update_record.filter = lambda row:{'u_notes': row.get('u_notes'),
   'subaccount': row.get('subaccount'),
   'u_sensitive_data': row.get('u_sensitive_data'),
   'sys_mod_count': row.get('sys_mod_count'),
   'active': row.get('active'),
   'name_of_body': row.get('name_of_body'),
   'sys_updated_on': row.get('sys_updated_on'),
   'sys_tags': row.get('sys_tags'),
   'u_consortium_id_value': row.get('u_consortium_id').get('value'),
   'u_consortium_id_link': row.get('u_consortium_id').get('link'),
   'sys_id': row.get('sys_id'),
   'sys_updated_by': row.get('sys_updated_by'),
   'sys_created_on': row.get('sys_created_on'),
   'domain': row.get('domain'),
   'u_approved': row.get('u_approved'),
   'region': row.get('region'),
   'u_type': row.get('u_type')}

    update_record.execute()


handler(None, None)
