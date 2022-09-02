`terraform` folder is the root module of terraform configuration, containing

- `backend.tf` - s3 bucket where terraform state is stored 
- `providers.tf` - default tags applied on all resources
- `variables.tf` -  variables referenced in root module
- `terraform.tfvars` - default values for variables (these values can be overridden dynamically: 
  ```terraform apply -var="name=value"```
- `main.tf` defines infrastructure sketched on the diagram [OFF SNOWFLAKE COMPUTING](../README.md).
   - **API Gateway**
   - **S3 buckets**
   - **Lambda functions**
   - **Scheduled events**
   - It uses custom modules, from [modules](./modules) folder.