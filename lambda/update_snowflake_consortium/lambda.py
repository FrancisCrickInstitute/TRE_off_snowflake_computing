import boto3

from shared.email_client import notification
from shared.update_snowflake_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update snowflake account table")
def handler(event, context):
    """Lambda function that send all consortium data from ServiceNow to Snowflake
    This helps metadata has more info for collaboration
    Lambda function send request to ServiceNow consortium API and get JSON data. Then, it parses
    to INSERT SQL query to write this data to Org_aadmin ccount table.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.endpoint = "x_tfci_snowflake_consortium"

    update_record.filter = lambda row: {'consortium_name': row.get('consortium_name'),
    'number': row.get('number'),
    'sys_created_by': row.get('sys_created_by'),
    'sys_created_on': row.get('sys_created_on'),
    'u_approved': row.get('consortium_name'),
    'u_approved_date': row.get('consortium_name'),
    'u_collaboration_description': row.get('consortium_name'),
    'u_start_date': row.get('consortium_name'),
    'u_working_title': row.get('consortium_name'),
    'sys_id': row.get('sys_id')}
    update_record.execute()


handler(None, None)
