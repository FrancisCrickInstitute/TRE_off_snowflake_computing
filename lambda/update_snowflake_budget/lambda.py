import boto3

from shared.email_client import notification
from shared.update_snowflake_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update snowflake budget table")
def handler(event, context):
    """Lambda function that send all budget data from ServiceNow to Snowflake
    This helps metadata has more info of budget control which is not native in Snowflake
    Lambda function send request to ServiceNow budget API and get JSON data. Then, it parses
    to INSERT SQL query to write this data to Org_aadmin ccount table.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.endpoint = "x_tfci_snowflake_budget"

    update_record.filter = lambda row: {'contract_period': row.get('contract_period'),
   'percent_subaccount_data_processor_by_contract_period': row.get('percent_subaccount_data_processor_by_contract_period'),
   'value_subaccount_data_sharer_by_contract_period': row.get('value_subaccount_data_sharer_by_contract_period'),
   'value_per_budget_control': row.get('value_per_budget_control'),
   'value_subaccount_data_loader_by_contract_period': row.get('value_subaccount_data_loader_by_contract_period'),
   'percent_budget_collaboration': row.get('percent_budget_collaboration'),
   'sys_updated_on': row.get('sys_updated_on'),
   'sub_account': row.get('sub_account').get('value'),
   'overall_budget': row.get('overall_budget'),
   'grant_code': row.get('grant_code'),
   'number': row.get('number'),
   'sys_id': row.get('sys_id'),
   'sys_updated_by': row.get('sys_updated_by'),
   'sys_created_on': row.get('sys_created_on'),
   'value_collab_experimenter_by_contract_period': row.get('value_collab_experimenter_by_contract_period'),
   'percent_budget_account': row.get('percent_budget_account'),
   'sys_created_by': row.get('sys_created_by'),
   'value_budget_account': row.get('value_budget_account'),
   'u_credits_for_collaboration': row.get('u_credits_for_collaboration'),
   'percent_subaccount_data_loader_by_contract_period': row.get('percent_subaccount_data_loader_by_contract_period'),
   'u_budget_control': row.get('u_budget_control'),
   'sys_mod_count': row.get('sys_mod_count'),
   'project_code': row.get('project_code'),
   'sys_tags': row.get('sys_tags'),
   'value_collab_data_curator_by_contract_period': row.get('value_collab_data_curator_by_contract_period'),
   'value_budget_collaboration': row.get('value_budget_collaboration'),
   'percent_subaccount_data_sharer_by_contract_period': row.get('percent_subaccount_data_sharer_by_contract_period'),
   'consortium_id': row.get('consortium_id').get('value'),
   'percent_collab_experimenter_by_contract_period': row.get('percent_collab_experimenter_by_contract_period'),
   'value_subaccount_data_processor_by_contract_period': row.get('value_subaccount_data_processor_by_contract_period'),
   'percent_collab_data_curator_by_contract_period': row.get('percent_collab_data_curator_by_contract_period')}
    
    update_record.execute()


handler(None, None)
