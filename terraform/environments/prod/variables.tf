variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.1.0.0/16"
}

# Database variables - Production settings
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "inventory_management"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "inventory_user"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = true
}

variable "db_deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

# Cache variables - Production settings
variable "cache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "cache_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

# SSL Certificate
variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
}

# ALB settings
variable "alb_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = true
}

# Container image variables
variable "api_gateway_image" {
  description = "Docker image for API Gateway service"
  type        = string
}

# Production scaling settings for API Gateway
variable "api_gateway_cpu" {
  description = "CPU units for API Gateway"
  type        = number
  default     = 512
}

variable "api_gateway_memory" {
  description = "Memory for API Gateway in MB"
  type        = number
  default     = 1024
}

variable "api_gateway_desired_count" {
  description = "Desired count for API Gateway"
  type        = number
  default     = 2
}

variable "api_gateway_min_capacity" {
  description = "Minimum capacity for API Gateway auto-scaling"
  type        = number
  default     = 2
}

variable "api_gateway_max_capacity" {
  description = "Maximum capacity for API Gateway auto-scaling"
  type        = number
  default     = 20
}