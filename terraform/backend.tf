terraform {
  backend "s3" {}
}

resource "aws_s3_bucket" "tf_backend" {
  bucket = "${var.project}-tfstate"
}

resource "aws_s3_bucket_versioning" "tf_versioning" {
  bucket = aws_s3_bucket.tf_backend.id

  versioning_configuration {
    status = "Enabled"
  }
}
