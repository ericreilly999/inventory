# Database Migration ECS Task Definition
# This task runs Alembic migrations before deployments

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# IAM role for migration task execution
resource "aws_iam_role" "migration_task_execution" {
  name = "${var.environment}-migration-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Attach ECS task execution policy
resource "aws_iam_role_policy_attachment" "migration_task_execution" {
  role       = aws_iam_role.migration_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow reading secrets for database credentials
resource "aws_iam_role_policy" "migration_secrets" {
  name = "${var.environment}-migration-secrets-policy"
  role = aws_iam_role.migration_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.database_secret_arn
      }
    ]
  })
}

# IAM role for migration task (container role)
resource "aws_iam_role" "migration_task" {
  name = "${var.environment}-migration-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# CloudWatch log group for migration task
resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${var.environment}/migration-task"
  retention_in_days = 7

  tags = var.tags
}

# ECS task definition for migrations
resource "aws_ecs_task_definition" "migration" {
  family                   = "${var.environment}-migration-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.migration_task_execution.arn
  task_role_arn            = aws_iam_role.migration_task.arn

  container_definitions = jsonencode([
    {
      name  = "migration"
      image = var.migration_image

      command = [
        "sh",
        "-c",
        "pip install --no-cache-dir alembic psycopg2-binary sqlalchemy pydantic pydantic-settings python-dotenv && alembic upgrade head"
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${var.database_secret_arn}:url::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.migration.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }
    }
  ])

  tags = var.tags
}
