variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "migration_image" {
  description = "Docker image to use for migrations (should contain alembic.ini and migrations/)"
  type        = string
}

variable "database_secret_arn" {
  description = "ARN of the Secrets Manager secret containing database credentials"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
