# Shared outputs

output "project_name" {
  description = "Name of the project"
  value       = var.project_name
}

output "common_tags" {
  description = "Common tags for all resources"
  value       = var.common_tags
}