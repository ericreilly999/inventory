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

  environment        = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  security_group_id = module.security.alb_security_group_id
  
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

# API Gateway Service
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
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids
  target_group_arn  = module.alb.api_gateway_target_group_arn

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
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

# User Service
module "user_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "user-service"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.user_service_image
  container_port  = 8001
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    }
  ]

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.rds.db_secret_arn}:password::"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "user-service"
  }
}

# Inventory Service
module "inventory_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "inventory-service"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.inventory_service_image
  container_port  = 8002
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    }
  ]

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.rds.db_secret_arn}:password::"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "inventory-service"
  }
}

# Location Service
module "location_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "location-service"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.location_service_image
  container_port  = 8003
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    }
  ]

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.rds.db_secret_arn}:password::"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:8003/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "location-service"
  }
}

# Reporting Service
module "reporting_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "reporting-service"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.reporting_service_image
  container_port  = 8004
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "DATABASE_URL"
      value = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_endpoint}/${var.db_name}"
    }
  ]

  secrets = [
    {
      name      = "DATABASE_PASSWORD"
      valueFrom = "${module.rds.db_secret_arn}:password::"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:8004/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "reporting-service"
  }
}

# UI Service
module "ui_service" {
  source = "../../modules/ecs-service"

  environment                      = var.environment
  service_name                    = "ui-service"
  cluster_id                      = module.ecs_cluster.cluster_id
  cluster_name                    = module.ecs_cluster.cluster_name
  task_execution_role_arn         = module.ecs_cluster.task_execution_role_arn
  task_role_arn                   = module.ecs_cluster.task_role_arn
  log_group_name                  = module.ecs_cluster.log_group_name
  service_discovery_namespace_id  = module.ecs_cluster.service_discovery_namespace_id

  container_image = var.ui_service_image
  container_port  = 80
  cpu            = 256
  memory         = 512
  desired_count  = 1

  security_group_ids = [module.security.ecs_security_group_id]
  subnet_ids        = module.networking.private_subnet_ids
  target_group_arn  = module.alb.ui_target_group_arn

  environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "API_GATEWAY_URL"
      value = "http://api-gateway.${var.environment}.inventory.local:8000"
    }
  ]

  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }

  tags = {
    Environment = var.environment
    Product     = "inventory-management"
    Service     = "ui-service"
  }
}