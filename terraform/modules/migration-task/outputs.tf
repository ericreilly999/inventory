output "task_definition_arn" {
  description = "ARN of the migration task definition"
  value       = aws_ecs_task_definition.migration.arn
}

output "task_definition_family" {
  description = "Family name of the migration task definition"
  value       = aws_ecs_task_definition.migration.family
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for migrations"
  value       = aws_cloudwatch_log_group.migration.name
}
