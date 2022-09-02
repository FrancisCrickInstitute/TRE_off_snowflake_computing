data aws_caller_identity current {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

###############
# API GATEWAY #
###############

module "api_gateway" {
  source  = "./modules/api-gateway"
  region  = var.region
  project = var.project
  env     = var.environment
}

######
# S3 #
######

module "setup_account_s3" {
  source = "./modules/s3"

  bucket = "${var.project}-setup-account-${var.environment}"

  lambda_arn   = module.create_account_lambda.arn
  lambda_name  = module.create_account_lambda.name
  gateway_role = module.api_gateway.role_name
  group        = aws_iam_group.servicenow.name
}

module "setup_experiment_s3" {
  source = "./modules/s3"

  bucket = "${var.project}-setup-experiment-${var.environment}"

  lambda_arn   = module.setup_experiment.arn
  lambda_name  = module.setup_experiment.name
  gateway_role = module.api_gateway.role_name
  group        = aws_iam_group.servicenow.name
}

module "setup_user_s3" {
  source = "./modules/s3"

  bucket = "${var.project}-setup-user-${var.environment}"

  lambda_arn   = module.setup_user.arn
  lambda_name  = module.setup_user.name
  gateway_role = module.api_gateway.role_name
  group        = aws_iam_group.servicenow.name
}

module "create_external_stage_s3" {
  source = "./modules/s3"

  bucket = "${var.project}-setup-external-stage-${var.environment}"

  lambda_arn   = module.create_external_stage.arn
  lambda_name  = module.create_external_stage.name
  gateway_role = module.api_gateway.role_name
  group        = aws_iam_group.servicenow.name
}

##########
# LAMBDA #
##########

module "create_account_lambda" {
  source = "./modules/lambda"

  folder = "lambda/create_account"
  name   = "${var.project}_create_account_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_account_lambda" {
  source = "./modules/lambda"

  folder = "lambda/setup_account"
  name   = "${var.project}_setup_account_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_metadata_lambda" {
  source = "./modules/lambda"

  folder = "lambda/setup_metadata"
  name   = "${var.project}_setup_metadata_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_okta_integration" {
  source = "./modules/lambda"

  folder = "lambda/setup_okta_integration"
  name   = "${var.project}_setup_okta_integration_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_experiment" {
  source = "./modules/lambda"

  folder = "lambda/setup_experiment"
  name   = "${var.project}_setup_experiment_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "create_external_stage" {
  source = "./modules/lambda"

  folder = "lambda/create_external_stage"
  name   = "${var.project}_create_external_stage_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_user" {
  source = "./modules/lambda"

  folder = "lambda/setup_user"
  name   = "${var.project}_setup_user_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "setup_okta_user" {
  source = "./modules/lambda"

  folder = "lambda/setup_okta_user"
  name   = "${var.project}_setup_okta_user_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_svn_account_records" {
  source = "./modules/lambda"

  folder = "lambda/update_svn_account_records"
  name   = "${var.project}_update_svn_account_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_svn_objects_records" {
  source = "./modules/lambda"

  folder = "lambda/update_svn_objects_records"
  name   = "${var.project}_update_svn_objects_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_svn_experiment_records" {
  source = "./modules/lambda"

  folder = "lambda/update_svn_experiment_records"
  name   = "${var.project}_update_svn_experiment_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_svn_user_records" {
  source = "./modules/lambda"

  folder = "lambda/update_svn_user_records"
  name   = "${var.project}_update_svn_user_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_svn_warehouse_records" {
  source = "./modules/lambda"

  folder = "lambda/update_svn_warehouse_records"
  name   = "${var.project}_update_svn_warehouse_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_snowflake_account_records" {
  source = "./modules/lambda"

  folder = "lambda/update_snowflake_account_records"
  name   = "${var.project}_update_snowflake_account_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_snowflake_consortium" {
  source = "./modules/lambda"

  folder = "lambda/update_snowflake_consortium"
  name   = "${var.project}_update_snowflake_consortium_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_snowflake_budget" {
  source = "./modules/lambda"

  folder = "lambda/update_snowflake_budget"
  name   = "${var.project}_update_snowflake_budget_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_snowflake_experiment" {
  source = "./modules/lambda"

  folder = "lambda/update_snowflake_experiment"
  name   = "${var.project}_update_snowflake_experiment_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "update_snowflake_user_records" {
  source = "./modules/lambda"

  folder = "lambda/update_snowflake_user_records"
  name   = "${var.project}_update_snowflake_user_records_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "alter_metadata" {
  source = "./modules/lambda"

  folder = "lambda/alter_metadata"
  name   = "${var.project}_alter_metadata_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

module "archive" {
  source = "./modules/lambda"

  folder = "lambda/archive"
  name   = "${var.project}_archive_${var.environment}"

  tag          = var.tag
  region       = var.region
  architecture = var.architecture
  env          = var.environment
  project      = var.project

  lambda_role_arn = module.lambda_role.arn
}

############
# POLICIES #
############

module "reader" {
  source   = "./modules/policy"
  name     = "reader"
  project  = var.project
  template = "./policy/reader.json.tpl"
}

module "admin" {
  source   = "./modules/policy"
  name     = "admin"
  project  = var.project
  template = "./policy/admin.json.tpl"
}

module "tester" {
  source   = "./modules/policy"
  name     = "tester"
  project  = var.project
  template = "./policy/tester.json.tpl"
}

#########
# ROLES #
#########

module "lambda_role" {
  source = "./modules/lambda_role"
}


#################
# DOCUMENTATION #
#################
module "documentation" {
  source      = "./modules/static-web"
  domain_name = "${var.project}-documentation-${var.environment}"
  content     = "../docs/build/html/"
}


###################
# SERVICENOW USER #
###################

resource "aws_iam_group" "servicenow" {
  name = "servicenow-s3-access-group"
}

data aws_iam_policy_document servicenow {
  statement {
    actions   = ["s3:*"]
    effect    = "Allow"
    resources = ["arn:aws:s3:::*"]
  }
  statement {
    actions = [
      "kms:GenerateDataKey"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource aws_iam_policy servicenow {
  name   = "servicenow-policy"
  path   = "/"
  policy = data.aws_iam_policy_document.servicenow.json
}

resource "aws_iam_group_policy_attachment" "servicenow" {
  policy_arn = aws_iam_policy.servicenow.arn
  group       = aws_iam_group.servicenow.name
}
