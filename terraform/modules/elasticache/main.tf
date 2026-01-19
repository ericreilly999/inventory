# ElastiCache parameter group
resource "aws_elasticache_parameter_group" "main" {
  family = "redis7"
  name   = "${var.environment}-inventory-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-redis-params"
  })
}

# ElastiCache replication group
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.environment}-inventory-redis"
  description                = "Redis cluster for inventory management system"

  # Node configuration
  node_type            = var.node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name

  # Cluster configuration
  num_cache_clusters = var.num_cache_nodes

  # Network configuration
  subnet_group_name  = var.cache_subnet_group_name
  security_group_ids = var.security_group_ids

  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result

  # Backup configuration
  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"

  # Automatic failover
  automatic_failover_enabled = var.num_cache_nodes > 1

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-redis"
  })
}

# Random auth token for Redis
resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# CloudWatch log group for Redis slow logs
resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/${var.environment}-inventory-redis/slow-log"
  retention_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-redis-slow-log"
  })
}

# Store Redis auth token in AWS Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name        = "${var.environment}/inventory-management/redis"
  description = "Redis auth token for inventory management system"

  tags = merge(var.tags, {
    Name = "${var.environment}-inventory-redis-secret"
  })
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    endpoint   = aws_elasticache_replication_group.main.primary_endpoint_address
    port       = aws_elasticache_replication_group.main.port
  })
}