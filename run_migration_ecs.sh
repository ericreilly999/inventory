#!/bin/bash
# Script to run database migration via ECS task
# This script runs migrations from within the VPC where the database is accessible

set -e

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-us-west-2}
CLUSTER_NAME="${ENVIRONMENT}-inventory-cluster"
MIGRATION_TASK="${ENVIRONMENT}-migration-task"

echo "========================================="
echo "Running Database Migration via ECS Task"
echo "========================================="
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "Cluster: $CLUSTER_NAME"
echo "Task: $MIGRATION_TASK"
echo ""

# Get the subnet and security group from an existing service
echo "Getting network configuration from inventory-service..."
SERVICE_INFO=$(aws ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "${ENVIRONMENT}-inventory-service" \
  --region "$AWS_REGION" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' \
  --output json)

if [ -z "$SERVICE_INFO" ] || [ "$SERVICE_INFO" = "null" ]; then
  echo "❌ Error: Could not get network configuration from inventory-service"
  exit 1
fi

SUBNETS=$(echo "$SERVICE_INFO" | jq -r '.subnets[0]')
SECURITY_GROUPS=$(echo "$SERVICE_INFO" | jq -r '.securityGroups[0]')

echo "Subnet: $SUBNETS"
echo "Security Group: $SECURITY_GROUPS"
echo ""

# Run the migration task
echo "Starting migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER_NAME" \
  --task-definition "$MIGRATION_TASK" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=DISABLED}" \
  --region "$AWS_REGION" \
  --query 'tasks[0].taskArn' \
  --output text)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" = "None" ]; then
  echo "❌ Error: Failed to start migration task"
  exit 1
fi

echo "Migration task started: $TASK_ARN"
echo "Waiting for task to complete..."
echo ""

# Wait for task to complete (timeout after 5 minutes)
aws ecs wait tasks-stopped \
  --cluster "$CLUSTER_NAME" \
  --tasks "$TASK_ARN" \
  --region "$AWS_REGION" \
  --max-attempts 30 \
  --delay 10

# Check task exit code
TASK_INFO=$(aws ecs describe-tasks \
  --cluster "$CLUSTER_NAME" \
  --tasks "$TASK_ARN" \
  --region "$AWS_REGION" \
  --query 'tasks[0]' \
  --output json)

EXIT_CODE=$(echo "$TASK_INFO" | jq -r '.containers[0].exitCode')
STOP_REASON=$(echo "$TASK_INFO" | jq -r '.stoppedReason // "Unknown"')

echo "========================================="
echo "Migration Task Results"
echo "========================================="
echo "Exit Code: $EXIT_CODE"
echo "Stop Reason: $STOP_REASON"
echo ""

if [ "$EXIT_CODE" = "0" ]; then
  echo "✅ Migration completed successfully!"
  echo ""
  echo "View logs at:"
  echo "https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups/log-group//ecs/$ENVIRONMENT/migration-task"
  exit 0
else
  echo "❌ Migration failed with exit code: $EXIT_CODE"
  echo ""
  echo "View logs at:"
  echo "https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups/log-group//ecs/$ENVIRONMENT/migration-task"
  echo ""
  echo "Common issues:"
  echo "  - Database credentials incorrect"
  echo "  - Network connectivity issues"
  echo "  - Migration script errors"
  exit 1
fi
