#!/bin/bash
# Script to deploy Lambda function for database seeding

FUNCTION_NAME="inventory-db-seeder"
REGION="us-west-2"

echo "Creating Lambda deployment package..."

# Create temporary directory
mkdir -p /tmp/lambda-seed
cp scripts/lambda_seed.py /tmp/lambda-seed/

# Install psycopg2 for Lambda
cd /tmp/lambda-seed
pip install psycopg2-binary -t .

# Create deployment package
zip -r lambda-seed.zip .

echo "Deploying Lambda function..."

# Create or update Lambda function
aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --runtime python3.9 \
    --role arn:aws:iam::290993374431:role/lambda-execution-role \
    --handler lambda_seed.lambda_handler \
    --zip-file fileb://lambda-seed.zip \
    --region $REGION \
    --vpc-config SubnetIds=subnet-0fd9dd82488ae1c81,subnet-0f81f198d3edc3a9d,SecurityGroupIds=sg-0c0263bc0bcda46ff \
    --timeout 60 \
    2>/dev/null || \
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda-seed.zip \
    --region $REGION

echo "Invoking Lambda function to seed database..."

# Invoke the function
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --payload '{}' \
    response.json

echo "Lambda response:"
cat response.json

# Cleanup
cd -
rm -rf /tmp/lambda-seed
rm -f response.json

echo "Database seeding completed!"