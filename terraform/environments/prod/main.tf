terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Product     = "inventory-management"
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Networking module
module "networking" {
  source = "../../modules/networking"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# Security module
module "security" {
  source = "../../modules/security"

  environment = var.environment
  vpc_id      = module.networking.vpc_id
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# RDS module
module "rds" {
  source = "../../modules/rds"

  environment            = var.environment
  vpc_id                = module.networking.vpc_id
  database_subnet_ids   = module.networking.database_subnet_ids
  db_subnet_group_name  = module.networking.database_subnet_group_name
  security_group_ids    = [module.security.rds_security_group_id]
  
  db_instance_class     = var.db_instance_class
  db_allocated_storage  = var.db_allocated_storage
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password
  multi_az             = var.db_multi_az
  deletion_protection  = var.db_deletion_protection
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# ElastiCache module
module "elasticache" {
  source = "../../modules/elasticache"

  environment            = var.environment
  vpc_id                = module.networking.vpc_id
  cache_subnet_ids      = module.networking.private_subnet_ids
  cache_subnet_group_name = module.networking.cache_subnet_group_name
  security_group_ids    = [module.security.elasticache_security_group_id]
  
  node_type             = var.cache_node_type
  num_cache_nodes       = var.cache_num_nodes
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# Application Load Balancer
module "alb" {
  source = "../../modules/alb"

  environment               = var.environment
  vpc_id                   = module.networking.vpc_id
  public_subnet_ids        = module.networking.public_subnet_ids
  security_group_id        = module.security.alb_security_group_id
  certificate_arn          = var.ssl_certificate_arn
  enable_deletion_protection = var.alb_deletion_protection
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# ECS Cluster
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"

  environment = var.environment
  vpc_id      = module.networking.vpc_id
  
  tags = {
    Environment = var.environment
    Product     = "inventory-management"
  }
}

# Production services with higher resource allocation
module "api_gateway_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "api-gateway"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.api_gateway_image
  container_port  = 8000
  cpu            = var.api_gateway_cpu
  memory         = var.api_gateway_memory
  desired_count  = var.api_gateway_desired_count

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids
  target_group_arn  = module.alb.api_gateway_target_group_arn

  min_capacity = var.api_gateway_min_capacity
  max_capacity = var.api_gateway_max_capacity

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}@${module.rds.db_endpoint}:${module.rds.db_port}/${var.db_name}"
    },
    {
      name  = "REDIS_URL"
      value = "redis://${module.elasticache.cache_endpoint}:${module.elasticache.cache_port}"
    }
  ]

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.rds.db_secret_arn}:password::"
    },
    {
      name      = "REDIS_AUTH_TOKEN"
      valueFrom = "${module.elasticache.cache_secret_arn}:auth_token::"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "api-gateway"
  }
}