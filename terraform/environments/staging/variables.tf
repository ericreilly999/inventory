variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.1.0.0/16"
}

# Database variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.small"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
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

# Cache variables
variable "cache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "cache_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# Container image variables
variable "api_gateway_image" {
  description = "Docker image for API Gateway service"
  type        = string
  default     = "inventory-management/api-gateway:latest"
}

variable "user_service_image" {
  description = "Docker image for User service"
  type        = string
  default     = "inventory-management/user-service:latest"
}

variable "inventory_service_image" {
  description = "Docker image for Inventory service"
  type        = string
  default     = "inventory-management/inventory-service:latest"
}

variable "location_service_image" {
  description = "Docker image for Location service"
  type        = string
  default     = "inventory-management/location-service:latest"
}

variable "reporting_service_image" {
  description = "Docker image for Reporting service"
  type        = string
  default     = "inventory-management/reporting-service:latest"
}

variable "ui_service_image" {
  description = "Docker image for UI service"
  type        = string
  default     = "inventory-management/ui-service:latest"
}
