#!/bin/bash
# Script to pull AWS CloudWatch logs for all services

# Default parameters
ENVIRONMENT=${1:-"dev"}
REGION=${2:-"us-east-1"}
MINUTES=${3:-60}

echo "Pulling AWS CloudWatch logs for environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Last $MINUTES minutes"

# Calculate start time (X minutes ago)
START_TIME=$(date -d "$MINUTES minutes ago" -u +"%Y-%m-%dT%H:%M:%S")

# Define services and their log groups
declare -A SERVICES=(
    ["api-gateway"]="/ecs/inventory-management/api-gateway"
    ["inventory-service"]="/ecs/inventory-management/inventory-service"
    ["location-service"]="/ecs/inventory-management/location-service"
    ["user-service"]="/ecs/inventory-management/user-service"
    ["reporting-service"]="/ecs/inventory-management/reporting-service"
    ["ui-service"]="/ecs/inventory-management/ui-service"
)

# Create logs directory if it doesn't exist
mkdir -p logs

for SERVICE in "${!SERVICES[@]}"; do
    LOG_GROUP="${SERVICES[$SERVICE]}"
    OUTPUT_FILE="logs/$SERVICE-aws.log"
    
    echo ""
    echo "Pulling logs for $SERVICE..."
    echo "Log Group: $LOG_GROUP"
    
    # Create service log directory
    mkdir -p "logs/$SERVICE"
    
    # Pull logs using AWS CLI
    if aws logs filter-log-events \
        --log-group-name "$LOG_GROUP" \
        --start-time "$START_TIME" \
        --region "$REGION" \
        --output text \
        --query 'events[*].[timestamp,message]' > "$OUTPUT_FILE" 2>/dev/null; then
        
        # Filter for errors and important messages
        ERROR_FILE="logs/$SERVICE-errors.log"
        grep -i -E "(ERROR|CRITICAL|FATAL|Exception|Traceback|Failed|Connection.*refused|Database.*error|Authentication.*failed)" "$OUTPUT_FILE" > "$ERROR_FILE" 2>/dev/null
        
        LOG_COUNT=$(wc -l < "$OUTPUT_FILE")
        ERROR_COUNT=$(wc -l < "$ERROR_FILE" 2>/dev/null || echo 0)
        
        echo "✓ $SERVICE: $LOG_COUNT total logs, $ERROR_COUNT errors"
        
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo "  Errors saved to: $ERROR_FILE"
        fi
    else
        echo "✗ Failed to pull logs for $SERVICE"
    fi
done

echo ""
echo "Log pull completed!"
echo "Check the logs/ directory for service logs"

# Show summary of errors found
echo ""
echo "=== ERROR SUMMARY ==="
for SERVICE in "${!SERVICES[@]}"; do
    ERROR_FILE="logs/$SERVICE-errors.log"
    if [ -f "$ERROR_FILE" ]; then
        ERROR_COUNT=$(wc -l < "$ERROR_FILE" 2>/dev/null || echo 0)
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo "$SERVICE: $ERROR_COUNT errors found"
        fi
    fi
done