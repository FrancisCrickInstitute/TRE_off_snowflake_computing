import json
import boto3
from shared.utils import template_to_yaml, apply

# set these parameters to test changes in the template

template = "03_setup_subaccount"
account_name = "collaboration"
json_input_path = "../test/inputs/account/collaboration.json"



secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
password = secrets_manager.get_secret_value(
    SecretId=account_name.upper()
)['SecretString']

org_name = secrets_manager.get_secret_value(
    SecretId="org_name"
)['SecretString']

sf_account = "{}-{}".format(org_name, account_name).lower()

with open(json_input_path, "r") as json_file:
    json_inputs = json.load(json_file)
    template_to_yaml(json_inputs, template)
    apply(template, sf_account=sf_account, sf_username="ACCOUNTADMIN_MAIN", sf_password=password,
          tasks_dir="../packages/tasks", revert=False)

