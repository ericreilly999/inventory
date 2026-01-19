# Shared variables across all environments

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "inventory-management"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Product   = "inventory-management"
    ManagedBy = "terraform"
  }
}

# Database configuration
variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "db_parameter_group_family" {
  description = "PostgreSQL parameter group family"
  type        = string
  default     = "postgres15"
}

# Cache configuration
variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_parameter_group_family" {
  description = "Redis parameter group family"
  type        = string
  default     = "redis7.x"
}

# Container configuration
variable "default_cpu" {
  description = "Default CPU units for containers"
  type        = number
  default     = 256
}

variable "default_memory" {
  description = "Default memory for containers in MB"
  type        = number
  default     = 512
}

# Auto-scaling configuration
variable "default_min_capacity" {
  description = "Default minimum capacity for auto-scaling"
  type        = number
  default     = 1
}

variable "default_max_capacity" {
  description = "Default maximum capacity for auto-scaling"
  type        = number
  default     = 10
}

variable "default_cpu_target" {
  description = "Default CPU target for auto-scaling"
  type        = number
  default     = 70
}

variable "default_memory_target" {
  description = "Default memory target for auto-scaling"
  type        = number
  default     = 80
}