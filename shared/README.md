**SHARED** package contains python modules used by lambda functions.

- **email** contains `EmailClient` class for sending notification emails to users created by **flows** and Snowflake admins.
It also contains **decorator** `email`, which sends `process started`, `process succeeded` and `process failed` notification automatically for each lambda function.
- **utils** contains several util methods, described in `docstrings`.
- **update_servicenow_records** is a strategy for updating ServiceNow tables.
- **update_snowflake_records** is a strategy for updating tables in Snowflake used in **Reporting**.
