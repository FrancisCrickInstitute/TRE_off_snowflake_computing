variable "runtime" {}
variable "timeout" {}
variable "repo" {}

variable "tag" {
  default = "latest"
}
variable region {
  default = "eu-west-2"
}
variable "architecture" {
  default = "arm64"
}

variable "environment" {
  default = "dev"
}

variable "project" {
  default = "tre"
}

variable "department" {
  default = "it-department"
}

variable "createdby" {
  default = "terraform-user"
}