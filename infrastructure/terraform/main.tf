# main.tf
provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "docs" {
  bucket = "kaiser-rag-docs-phase1"
}
