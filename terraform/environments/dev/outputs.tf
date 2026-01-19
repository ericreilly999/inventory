output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.networking.database_subnet_ids
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.alb.alb_zone_id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "elasticache_endpoint" {
  description = "ElastiCache cluster endpoint"
  value       = module.elasticache.cache_endpoint
  sensitive   = true
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS services"
  value       = module.security.ecs_security_group_id
}
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs_cluster.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs_cluster.cluster_arn
}

output "service_discovery_namespace_name" {
  description = "Name of the service discovery namespace"
  value       = module.ecs_cluster.service_discovery_namespace_name
}

output "api_gateway_service_name" {
  description = "Name of the API Gateway ECS service"
  value       = module.api_gateway_service.service_name
}

output "user_service_name" {
  description = "Name of the User ECS service"
  value       = module.user_service.service_name
}

output "inventory_service_name" {
  description = "Name of the Inventory ECS service"
  value       = module.inventory_service.service_name
}

output "location_service_name" {
  description = "Name of the Location ECS service"
  value       = module.location_service.service_name
}

output "reporting_service_name" {
  description = "Name of the Reporting ECS service"
  value       = module.reporting_service.service_name
}

output "ui_service_name" {
  description = "Name of the UI ECS service"
  value       = module.ui_service.service_name
}