import boto3

from shared.email_client import notification
from shared.update_snowflake_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update snowflake experiment table")
def handler(event, context):
    """Lambda function that send all experiment data from ServiceNow to Snowflake
    This helps metadata has more info for reporting like budget account, approve ...
    Lambda function send request to ServiceNow experiment API and get JSON data. Then, it parses
    to INSERT SQL query to write this data to Org_aadmin ccount table.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.endpoint = "x_tfci_snowflake_experiment_records"

    update_record.filter = lambda row:{'active': row.get('active'),
   'name_of_body': row.get('name_of_body').get('value'),
   'number': row.get('number'),
   'region': row.get('active'),
   'sys_created_by': row.get('sys_created_by'),
   'sys_created_on': row.get('sys_created_on'),
   'sys_id': row.get('sys_id'),
   'sys_mod_count': row.get('sys_mod_count'),
   'sys_tags': row.get('sys_tags'),
   'sys_updated_by': row.get('sys_updated_by'),
   'sys_updated_on': row.get('sys_updated_on'),
   'u_approved': row.get('u_approved'),
   'u_approved_date': row.get('u_approved_date'),
   'u_approver_username': row.get('u_approver_username'),
   'u_budget_account': row.get('u_budget_account').get('value'),
   'u_consortium_id': row.get('u_consortium_id').get('value'),
   'u_experiment_description': '',
   'u_experiment_end_date': row.get('u_experiment_end_date'),
   'u_experiment_name': row.get('u_experiment_name'),
   'u_experiment_start_date': row.get('u_experiment_start_date'),
   'u_notify_percent': row.get('u_notify_percent')}

    update_record.execute()


handler(None, None)
