import boto3
import json

import pytest
from botocore.config import Config

config = Config(
    read_timeout=400,
    connect_timeout=400,
    retries={"max_attempts": 0}
)
lambda_client = boto3.client('lambda', config=config)

env = "dev"
project = "tre"

s3 = boto3.resource("s3")
bucket_name = 'new-just-in-case-2'
region_name = "eu-west-2"
local = {'LocationConstraint': region_name}
try:
    bucket = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=local)
except:
    bucket = s3.Bucket(bucket_name)

payload = {
    "Records": [
        {
            "s3": {
                "bucket": {
                    "name": bucket_name
                },
                "object": {}
            }
        }
    ],
    "Test": True,
    "Revert": False
}

accounts = [
    "inputs/account/collaboration.json",
    "inputs/account/lab.json"
]

experiments = [
    "inputs/experiment/experiment.json"
]

users = [
    "inputs/user/add_user.json",
    "inputs/user/add_role.json",
    "inputs/user/remove_role.json",
    "inputs/user/delete_user.json"
]


def setup():
    global bucket
    try:
        bucket = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=local)
    except:
        bucket = s3.Bucket(bucket_name)


def run(files, function_name, revert=False):
    payload["Revert"] = revert
    for file in files:
        s3.Object(bucket_name, file).put(Body=open(file, 'rb'))
        payload["Records"][0]["s3"]["object"]["key"] = file
        response = lambda_client.invoke(FunctionName=function_name,
                                        InvocationType='RequestResponse',
                                        Payload=json.dumps(payload))

        outcome = json.loads(response['Payload'].read().decode())
        assert outcome['status'] == 'success', outcome['message']


@pytest.mark.order(1)
def test_setup_accounts():
    run(files=accounts, function_name=f"${project}_setup_account_${env}")


@pytest.mark.order(2)
def test_setup_metadata():
    run(files=accounts, function_name=f"${project}_setup_metadata_${env}")


@pytest.mark.order(3)
def test_setup_experiments():
    run(files=experiments, function_name=f"${project}_setup_experiment_${env}")


@pytest.mark.order(4)
def test_setup_users():
    run(files=users, function_name=f"${project}_setup_user_${env}")


@pytest.mark.order(5)
def test_revert_experiments():
    run(files=experiments, function_name=f"${project}_setup_experiment_${env}", revert=True)


@pytest.mark.order(6)
def test_revert_metadata():
    run(files=accounts, function_name=f"${project}_setup_metadata_${env}", revert=True)


@pytest.mark.order(7)
def test_revert_accounts():
    run(files=accounts, function_name=f"${project}_setup_account_${env}", revert=True)


def teardown():
    global bucket
    try:
        bucket.objects.all().delete()
        bucket.delete()
    except:
        pass
