terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.30.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

############################
# S3 VECTOR BUCKET
############################

resource "aws_s3vectors_bucket" "this" {
  bucket_name = "alex-vectors-${data.aws_caller_identity.current.account_id}"

  encryption {
    type = "SSE-S3"
  }

  tags = var.tags
}

############################
# VECTOR INDEX
############################

resource "aws_s3vectors_index" "financial_research" {
  bucket_name = aws_s3vectors_bucket.this.bucket_name
  index_name  = var.index_name

  dimension = var.vector_dimension

  distance_metric = var.distance_metric
}
