output "vector_bucket_name" {
  description = "S3 Vector bucket name"
  value       = aws_s3vectors_bucket.this.bucket_name
}

output "vector_index_name" {
  description = "Vector index name"
  value       = aws_s3vectors_index.financial_research.index_name
}

output "vector_index_dimension" {
  value = aws_s3vectors_index.financial_research.dimension
}

output "vector_index_distance_metric" {
  value = aws_s3vectors_index.financial_research.distance_metric
}
