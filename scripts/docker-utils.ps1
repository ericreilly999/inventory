# Docker Utilities for Inventory Management System
# PowerShell version for Windows environments

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Environment = "development",
    
    [Parameter(Position=2)]
    [string]$Service = ""
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker and try again."
        exit 1
    }
}

# Function to create log directories
function New-LogDirectories {
    Write-Status "Creating log directories..."
    $logDirs = @("api-gateway", "inventory-service", "location-service", "user-service", "reporting-service", "ui-service")
    
    foreach ($dir in $logDirs) {
        $path = "logs/$dir"
        if (!(Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
        }
    }
    Write-Success "Log directories created"
}

# Function to build all images
function Build-Images {
    Write-Status "Building Docker images..."
    docker-compose build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All images built successfully"
    } else {
        Write-Error "Failed to build images"
        exit 1
    }
}

# Function to start services
function Start-Services {
    param([string]$Env = "development")
    
    Write-Status "Starting services in $Env environment..."
    New-LogDirectories
    
    if ($Env -eq "production") {
        docker-compose -f docker-compose.prod.yml up -d
    } else {
        docker-compose up -d
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully"
    } else {
        Write-Error "Failed to start services"
        exit 1
    }
}

# Function to stop services
function Stop-Services {
    param([string]$Env = "development")
    
    Write-Status "Stopping services..."
    
    if ($Env -eq "production") {
        docker-compose -f docker-compose.prod.yml down
    } else {
        docker-compose down
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services stopped successfully"
    } else {
        Write-Error "Failed to stop services"
        exit 1
    }
}

# Function to restart services
function Restart-Services {
    param([string]$Env = "development")
    
    Write-Status "Restarting services..."
    Stop-Services $Env
    Start-Services $Env
}

# Function to show service status
function Show-Status {
    Write-Status "Service status:"
    docker-compose ps
}

# Function to show logs
function Show-Logs {
    param([string]$ServiceName = "")
    
    if ([string]::IsNullOrEmpty($ServiceName)) {
        docker-compose logs -f
    } else {
        docker-compose logs -f $ServiceName
    }
}

# Function to run health checks
function Test-Health {
    Write-Status "Running health checks..."
    
    $services = @(
        @{Name="api-gateway"; Port=8000},
        @{Name="inventory-service"; Port=8001},
        @{Name="location-service"; Port=8002},
        @{Name="user-service"; Port=8003},
        @{Name="reporting-service"; Port=8004},
        @{Name="ui-service"; Port=8005}
    )
    
    foreach ($service in $services) {
        Write-Status "Checking $($service.Name) on port $($service.Port)..."
        
        $timeout = 60
        $counter = 0
        $healthy = $false
        
        while ($counter -lt $timeout) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "$($service.Name) is healthy"
                    $healthy = $true
                    break
                }
            }
            catch {
                # Service not ready yet, continue waiting
            }
            
            $counter++
            Start-Sleep -Seconds 1
        }
        
        if (-not $healthy) {
            Write-Error "$($service.Name) health check failed after $timeout seconds"
        }
    }
}

# Function to clean up Docker resources
function Remove-DockerResources {
    Write-Status "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    Write-Success "Cleanup completed"
}

# Function to show help
function Show-Help {
    Write-Host "Docker Utilities for Inventory Management System" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\docker-utils.ps1 [COMMAND] [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  build                 Build all Docker images"
    Write-Host "  start [env]          Start services (env: development|production, default: development)"
    Write-Host "  stop [env]           Stop services (env: development|production, default: development)"
    Write-Host "  restart [env]        Restart services (env: development|production, default: development)"
    Write-Host "  status               Show service status"
    Write-Host "  logs [service]       Show logs (all services if no service specified)"
    Write-Host "  health               Run health checks on all services"
    Write-Host "  cleanup              Clean up Docker resources (containers, images, volumes, networks)"
    Write-Host "  help                 Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\docker-utils.ps1 start                    # Start services in development mode"
    Write-Host "  .\scripts\docker-utils.ps1 start production         # Start services in production mode"
    Write-Host "  .\scripts\docker-utils.ps1 logs api-gateway         # Show logs for api-gateway service"
    Write-Host "  .\scripts\docker-utils.ps1 health                   # Run health checks"
}

# Main script logic
function Main {
    if (-not (Test-Docker)) {
        return
    }
    
    switch ($Command.ToLower()) {
        "build" {
            Build-Images
        }
        "start" {
            Start-Services $Environment
        }
        "stop" {
            Stop-Services $Environment
        }
        "restart" {
            Restart-Services $Environment
        }
        "status" {
            Show-Status
        }
        "logs" {
            Show-Logs $Service
        }
        "health" {
            Test-Health
        }
        "cleanup" {
            Remove-DockerResources
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "Unknown command: $Command"
            Show-Help
            exit 1
        }
    }
}

# Run main function
Main