variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "index_name" {
  description = "Vector index name"
  type        = string
  default     = "financial-research"
}

variable "vector_dimension" {
  description = "Embedding vector dimension"
  type        = number
  default     = 384
}

variable "distance_metric" {
  description = "Distance metric for vector search"
  type        = string
  default     = "COSINE"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    Project = "alex"
    Type    = "vector-store"
  }
}
