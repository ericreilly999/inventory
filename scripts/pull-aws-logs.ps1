#!/usr/bin/env pwsh
# Script to pull AWS CloudWatch logs for all services

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1",
    [int]$Minutes = 60
)

Write-Host "Pulling AWS CloudWatch logs for environment: $Environment" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Green
Write-Host "Last $Minutes minutes" -ForegroundColor Green

# Calculate start time (X minutes ago)
$StartTime = (Get-Date).AddMinutes(-$Minutes).ToString("yyyy-MM-ddTHH:mm:ss")

# Define services and their log groups
$Services = @{
    "api-gateway" = "/ecs/inventory-management/api-gateway"
    "inventory-service" = "/ecs/inventory-management/inventory-service"
    "location-service" = "/ecs/inventory-management/location-service"
    "user-service" = "/ecs/inventory-management/user-service"
    "reporting-service" = "/ecs/inventory-management/reporting-service"
    "ui-service" = "/ecs/inventory-management/ui-service"
}

# Create logs directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

foreach ($Service in $Services.Keys) {
    $LogGroup = $Services[$Service]
    $OutputFile = "logs/$Service-aws.log"
    
    Write-Host "`nPulling logs for $Service..." -ForegroundColor Yellow
    Write-Host "Log Group: $LogGroup" -ForegroundColor Gray
    
    try {
        # Create service log directory
        New-Item -ItemType Directory -Force -Path "logs/$Service" | Out-Null
        
        # Pull logs using AWS CLI
        $LogCommand = "aws logs filter-log-events --log-group-name `"$LogGroup`" --start-time `"$StartTime`" --region $Region --output text --query 'events[*].[timestamp,message]'"
        
        Write-Host "Executing: $LogCommand" -ForegroundColor Gray
        
        $LogOutput = Invoke-Expression $LogCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Save raw logs
            $LogOutput | Out-File -FilePath $OutputFile -Encoding UTF8
            
            # Filter for errors and important messages
            $ErrorFile = "logs/$Service-errors.log"
            $LogOutput | Where-Object { 
                $_ -match "ERROR|CRITICAL|FATAL|Exception|Traceback|Failed|Connection.*refused|Database.*error|Authentication.*failed" 
            } | Out-File -FilePath $ErrorFile -Encoding UTF8
            
            $LogCount = ($LogOutput | Measure-Object).Count
            $ErrorCount = (Get-Content $ErrorFile -ErrorAction SilentlyContinue | Measure-Object).Count
            
            Write-Host "Success $Service - $LogCount total logs, $ErrorCount errors" -ForegroundColor Green
            
            if ($ErrorCount -gt 0) {
                Write-Host "  Errors saved to: $ErrorFile" -ForegroundColor Red
            }
        } else {
            Write-Host "Failed to pull logs for $Service" -ForegroundColor Red
            Write-Host "Error: $LogOutput" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Exception pulling logs for $Service - $_" -ForegroundColor Red
    }
}

Write-Host "`nLog pull completed!" -ForegroundColor Green
Write-Host "Check the logs/ directory for service logs" -ForegroundColor Yellow

# Show summary of errors found
Write-Host "`n=== ERROR SUMMARY ===" -ForegroundColor Red
foreach ($Service in $Services.Keys) {
    $ErrorFile = "logs/$Service-errors.log"
    if (Test-Path $ErrorFile) {
        $ErrorCount = (Get-Content $ErrorFile -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($ErrorCount -gt 0) {
            Write-Host "$Service - $ErrorCount errors found" -ForegroundColor Red
        }
    }
}