import json
import boto3
import requests
import snowflake.connector


class UpdateRecord:
    """
    Strategy for querying Snowflake metadata and updating corresponding tables in ServiceNow.

    Attributes
    ----------
    svn_user: str
        username for ServiceNow
    svn_password: str
        password for ServiceNow user
    sf_account: str
        Snowflake account name
    sf_username: str
        Snowflake user
    sf_password: str
        password for Snowflake user
    """
    def __init__(self, region="eu-west-2"):
        """
        Obtains from secrets all necessary credentials to login into ServiceNow and Snowflake.
        :param region: AWS region with Secrets Manager
        """
        secrets_manager = boto3.client('secretsmanager', region_name=region)

        self.svn_user = secrets_manager.get_secret_value(
            SecretId="svn_user"
        )['SecretString']
        self.svn_password = secrets_manager.get_secret_value(
            SecretId="svn_password"
        )['SecretString']

        org_name = secrets_manager.get_secret_value(
            SecretId="org_name"
        )['SecretString']
        self.sf_account = "{}-org_admin".format(org_name)
        self.sf_username = "ACCOUNTADMIN_MAIN"
        self.sf_password = secrets_manager.get_secret_value(
            SecretId="ACCOUNTADMIN_MAIN"
        )['SecretString']

        self._commands = []
        self._attributes = []
        self._endpoint = ""

    @property
    def commands(self):
        """
        Getter for commands.
        :return: list of commands to be executed in Snowflake.
        """
        return self._commands

    @commands.setter
    def commands(self, commands):
        """
        Setter for commands.
        :param commands: List of commands to be executed in Snowflake.
        """
        self._commands = commands

    @property
    def attributes(self):
        """
        Getter for attributes.
        :return: List of attributes that needs to be updated in ServiceNow table.
        """
        return self._attributes

    @attributes.setter
    def attributes(self, attributes):
        """
        Setter for attributes.
        :param attributes: List of attributes that needs to be updated in ServiceNow table.
        """
        self._attributes = attributes

    @property
    def endpoint(self):
        """
        Getter for endpoint.
        :return: Endpoint in ServiceNow that corresponds to the table that is updated.
        """
        return self._endpoint

    @endpoint.setter
    def endpoint(self, endpoint):
        """
        Setter for endpoint.
        :param endpoint: Endpoint in ServiceNow that corresponds to the table that is updated.
        """
        self._endpoint = endpoint

    def execute(self):
        """
        Executes the update strategy. Queries metadata from Snowflake and updates the corresponding table in ServiceNow.
        """
        if not self.commands:
            raise Exception("Error! List of commands needs to be provided!")
        if not self.attributes:
            raise Exception("Error! List of attributes needs to be provided!")
        if not self.endpoint:
            raise Exception("Error! An endpoint needs to be provided!")

        ctx = snowflake.connector.connect(
            user=self.sf_username,
            password=self.sf_password,
            account=self.sf_account
        )
        cs = ctx.cursor()

        for command in self.commands:
            print("Execute command")
            cs.execute(command)
        table = cs.fetchall()

        cs.close()
        ctx.close()

        data = [{attribute: row[index] for index, attribute in enumerate(self.attributes)} for row in table]

        if not data:
            raise Exception("No data obtained for a specified query!")

        records = json.dumps({"records": data})

        url = 'https://<service-now-endpoint>/insertMultiple'

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        requests.post(url, auth=(self.svn_user, self.svn_password), headers=headers, data=records)
