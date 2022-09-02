import boto3
import requests
import snowflake.connector


class UpdateRecord:
    """
    Strategy to query data from ServiceNow and update metadata tables in Snowflake.

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
        self.filter = lambda x: x
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
    def filter(self):
        """
        Getter for filter function.
        :return: Function that transforms data obtained from ServiceNow into table in Snowflake.
        """
        return self._filter

    @filter.setter
    def filter(self, filter):
        """
        Setter for filter function.
        :param filter: Function that transforms data obtained from ServiceNow into table in Snowflake.
        """
        self._filter = filter

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
        if not self.endpoint:
            raise Exception("Error! An endpoint needs to be provided!")

        url = f'https://<servicenow-endpoint>'

        response = requests.get(url=url, auth=(self.svn_user, self.svn_password))

        full_table = response.json()['result']

        print('full table ', full_table)

        table = list(map(self.filter, full_table))

        print(table)
        
        self.commands = [
            'use role ACCOUNTADMIN;',
            'use warehouse CORE_WH;',
            'TRUNCATE TABLE ORG_ADMIN_DB.ADMIN_SCH.{};'.format(self.endpoint),
            'insert into ORG_ADMIN_DB.ADMIN_SCH.{} values {};'.format(
                self.endpoint,
                "".join(str(tuple(map(lambda x: str(x), a.values()))) + ',' for a in table)[:-1]
            )
        ]
        
        ctx = snowflake.connector.connect(
            user=self.sf_username,
            password=self.sf_password,
            account=self.sf_account
        )
        cs = ctx.cursor()
        for command in self.commands:
            cs.execute(command)
        table = cs.fetchall()
