import boto3

from shared.email_client import notification
from shared.update_servicenow_records import UpdateRecord

secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")


@notification(secrets_manager=secrets_manager, function_name="update account record")
def handler(event, context):
    """Lambda function that send all objects data from Snowflake to Service Now.
    This helps Service Now forms filter for archive process. Users have options to 
    choose what to archive
    Lambda function runs a query then format as Json and send to Service Now API.
    Args:
        None
    """
    update_record = UpdateRecord()

    update_record.commands = [
        'use role ACCOUNTADMIN;',
        'use warehouse CORE_WH;',
        'select * from '
        'ORG_ADMIN_DB.ADMIN_SCH.UPDATE_SVN_OBJECT_RECORDS;'
    ]
    update_record.attributes = [
        "consortium_id",
        "name_of_body",
        "database_name",
        "schema",
        "table_name",
        "active_bytes",
        "experiment",
        "experiment_start_date",
        "table_dropped_flg",
        "database_created",
        "schema_created",
        "table_created"
    ]

    update_record.endpoint = "x_tfci_snowflake_objects_import"

    update_record.execute()


handler(None, None)
