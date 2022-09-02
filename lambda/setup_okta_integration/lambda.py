import boto3
from asyncio import run
import snowflake.connector
import okta.models as models
from shared.email_client import notification

from client import OktaClient

s3 = boto3.client('s3')
secrets_manager = boto3.client('secretsmanager', region_name="eu-west-2")
lambda_client = boto3.client('lambda')
events = boto3.client('events')


@notification(secrets_manager=secrets_manager, function_name="setup okta integration")
def handler(event, context):
    """
    Create integration between Snowflake and Okta.

    First, creates SAML app with the name Snowflake - <Account Name>.
    Then create group with name snowflake_<Account Name>, and assign app to the group.

    Obtains app metadata, and based on metadata, CREATE SECURITY INTEGRATION in Snowflake.

    Args:
        event(dict): contains ACCOUNT_NAME, corresponding to Snowflake account to integrate with Okta.

    """
    account_name = event["ACCOUNT_NAME"]
    url_path = get_url_path(account_name)
    print("url_pat", url_path)
    run(async_handler(account_name, url_path))


def get_url_path(account_name):
    account_password = secrets_manager.get_secret_value(
        SecretId=account_name.upper()
    )['SecretString']

    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']

    account = f"{org_name}-{account_name}"

    ctx = snowflake.connector.connect(
        user="ACCOUNTADMIN_MAIN",
        password=account_password,
        account=account
    )
    cs = ctx.cursor()

    cs.execute("use role accountadmin;")

    cs.execute("select current_account();")
    locator = cs.fetchone()[0].lower()

    cs.execute("select current_region();")
    reg = cs.fetchone()[0].lower().split('_')

    cloud = reg.pop(0)
    region = "-".join(reg)

    return f"{locator.lower()}.{region}.{cloud}"


async def async_handler(account_name, account_locator):
    okta_token = secrets_manager.get_secret_value(
        SecretId="okta_token"
    )['SecretString']

    okta_url = secrets_manager.get_secret_value(
        SecretId="okta_url"
    )['SecretString']

    entity_id, acs, x509cert = await setup_okta(okta_url, okta_token, account_locator, account_name)
    setup_snowflake(account_name, entity_id, acs, x509cert)


async def setup_okta(okta_url, okta_token, url_path, account_name):
    okta_client = OktaClient({
        'orgUrl': okta_url,
        'token': okta_token
    })

    saml_sign_on = models.SamlApplicationSettingsSignOn({
        "defaultRelayState": "",
        "ssoAcsUrl": f"https://{url_path}.snowflakecomputing.com/fed/login",
        "idpIssuer": "http://www.okta.com/${org.externalKey}",
        "audience": f"https://{url_path}.snowflakecomputing.com",
        "recipient": f"https://{url_path}.snowflakecomputing.com/fed/login",
        "destination": f"https://{url_path}.snowflakecomputing.com/fed/login",
        "subjectNameIdTemplate": "${user.userName}",
        "subjectNameIdFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        "responseSigned": True,
        "assertionSigned": True,
        "signatureAlgorithm": "RSA_SHA256",
        "digestAlgorithm": "SHA256",
        "honorForceAuthn": True,
        "authnContextClassRef": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
        "spIssuer": None,
        "requestCompressed": False,
        "attributeStatements": [],
        "inlineHooks": [],
        "allowMultipleAcsEndpoints": False,
        "acsEndpoints": [],
        "slo": {
            "enabled": False
        }
    })
    settings = models.SamlApplicationSettings({
        "signOn": saml_sign_on
    })

    saml_app_model = models.SamlApplication({
        "label": f"Snowflake - {account_name}",
        "accessibility": {
            "selfService": False,
            "errorRedirectUrl": None,
            "loginRedirectUrl": None
        },
        "visibility": {
            "autoSubmitToolbar": False,
            "hide": {
                "iOS": False,
                "web": False
            }
        },
        "settings": settings
    })

    # CREATE APPLICATION
    app, resp, err = await okta_client.create_application(saml_app_model)

    # CREATE GROUP
    group_profile = models.GroupProfile({
        'name': f"snowflake_{account_name}"
    })
    group_model = models.Group({
        'profile': group_profile
    })
    group, resp, err = await okta_client.create_group(group_model)

    # ASSIGN APP TO GROUP
    await okta_client.create_application_group_assignment(app.id, group.id, {})

    # ADD GROUP_ID TO SECRETS
    secrets_manager.create_secret(
        Name=f"okta_{account_name.lower()}_group_id",
        SecretString=group.id
    )

    # RETRIEVE APPLICATION'S METADATA: entity_id, acs, x509cert
    meta, resp, err = await okta_client.get_saml_metadata_for_application(appId=app.id, kid=app.credentials.signing.kid)

    entity_id = meta["mdEntityDescriptor"]["entityId"]
    acs = meta["mdEntityDescriptor"]["mdIdpssoDescriptor"]["mdSingleSignOnService"][0]["@Location"]
    x509cert = meta["mdEntityDescriptor"]["mdIdpssoDescriptor"]["mdKeyDescriptor"]["dsKeyInfo"]["dsX509Data"][
        "dsX509Certificate"].replace("\n", "")

    return entity_id, acs, x509cert


def setup_snowflake(account_name, entity_id, acs, x509cert):
    account_password = secrets_manager.get_secret_value(
        SecretId=account_name.upper()
    )['SecretString']

    org_name = secrets_manager.get_secret_value(
        SecretId="org_name"
    )['SecretString']
    account = f"{org_name}-{account_name}".lower()

    ctx = snowflake.connector.connect(
        user="ACCOUNTADMIN_MAIN",
        password=account_password,
        account=account
    )
    cs = ctx.cursor()

    commands = [
        "use role accountadmin;",
        f"""CREATE SECURITY INTEGRATION OKTAINTEGRATION
            type = saml2
            enabled = true
            saml2_issuer = '{entity_id}'
            saml2_sso_url = '{acs}'
            saml2_provider = 'OKTA'
            saml2_x509_cert='{x509cert}'
            saml2_sp_initiated_login_page_label = 'OKTA SSO'
            saml2_enable_sp_initiated = true;""",
        f"alter security integration OKTAINTEGRATION set saml2_snowflake_acs_url = 'https://{account}.snowflakecomputing.com/fed/login';",
        f"alter security integration OKTAINTEGRATION set saml2_snowflake_issuer_url = 'https://{account}.snowflakecomputing.com';"
    ]

    for command in commands:
        cs.execute(command)
