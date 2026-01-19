output "cache_cluster_id" {
  description = "ElastiCache cluster ID"
  value       = aws_elasticache_replication_group.main.id
}

output "cache_endpoint" {
  description = "ElastiCache primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "cache_port" {
  description = "ElastiCache port"
  value       = aws_elasticache_replication_group.main.port
}

output "cache_secret_arn" {
  description = "ARN of the Redis secret in Secrets Manager"
  value       = aws_secretsmanager_secret.redis_auth_token.arn
}

output "cache_secret_name" {
  description = "Name of the Redis secret in Secrets Manager"
  value       = aws_secretsmanager_secret.redis_auth_token.name
}