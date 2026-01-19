# Inventory Management System

A comprehensive microservices-based inventory management system built with Python FastAPI backend, React TypeScript frontend, and deployed on AWS Fargate with full CI/CD pipeline.

## 🚀 Live Demo

**Production URL**: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/

**Demo Credentials**:
- Username: `admin`
- Password: `admin`

## ✨ Features

### Current (Working)
- ✅ **User Authentication & Authorization**: JWT-based auth with role-based permissions
- ✅ **Modern React UI**: Material-UI based responsive interface
- ✅ **Microservices Architecture**: Scalable service-oriented design
- ✅ **AWS Cloud Deployment**: Fully deployed on AWS Fargate with RDS and ElastiCache
- ✅ **Infrastructure as Code**: Complete Terraform configuration
- ✅ **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- ✅ **Comprehensive Testing**: Unit, integration, and property-based tests

### In Development (WIP)
- 🚧 **Inventory Management**: Parent/child item tracking and relationships
- 🚧 **Location Management**: Multi-level location hierarchy and item movements
- 🚧 **Reporting & Analytics**: Real-time dashboards and custom reports
- 🚧 **Audit Logging**: Complete audit trail for all operations

## 🏗️ Architecture

The system consists of the following microservices:

- **API Gateway Service**: Central entry point, routing, and rate limiting
- **User Service**: Authentication, authorization, and user management
- **Inventory Service**: Parent items, child items, and relationships (WIP)
- **Location Service**: Locations, location types, and item movements (WIP)
- **Reporting Service**: Analytics, reports, and dashboards (WIP)
- **UI Service**: React-based web interface

## 🛠️ Technology Stack

### Backend
- **Python 3.11+** with **FastAPI** framework
- **PostgreSQL 15** for primary data storage
- **Redis 7** for caching and session management
- **SQLAlchemy** ORM with Alembic migrations
- **JWT** authentication with bcrypt password hashing
- **Pydantic** for data validation and serialization

### Frontend
- **React 18** with **TypeScript**
- **Material-UI (MUI)** component library
- **React Router** for navigation
- **Axios** for API communication

### Infrastructure
- **AWS Fargate** for container orchestration
- **Application Load Balancer** for traffic distribution
- **Amazon RDS PostgreSQL** for managed database
- **Amazon ElastiCache Redis** for managed caching
- **Amazon ECR** for container registry
- **Terraform** for Infrastructure as Code

### DevOps
- **Docker** for containerization
- **GitHub Actions** for CI/CD
- **Poetry** for Python dependency management
- **pytest** with property-based testing (Hypothesis)

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ (for UI development)
- Poetry (for Python dependency management)
- Docker and Docker Compose
- AWS CLI (for deployment)
- Terraform (for infrastructure management)

## 🚀 Quick Start

### Option 1: Use Live Demo
Visit the live demo at: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/
- Username: `admin`
- Password: `admin`

### Option 2: Local Development Setup

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd inventory-management-system
```

#### 2. Install Dependencies
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install Python dependencies
poetry install

# Install UI dependencies (for frontend development)
cd services/ui
npm install
cd ../..
```

#### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# Update database credentials, JWT secret, etc.
```

#### 4. Start Development Environment
```bash
# Start all services with Docker Compose
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

#### 5. Database Setup
```bash
# Run database migrations
poetry run alembic upgrade head

# Create admin user (optional - can also use the API)
python scripts/create_admin_user.py
```

#### 6. Access the Application
- **Web UI**: http://localhost:8005
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Development Workflow

### Running Services Locally

#### All Services (Recommended)
```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs for specific service
docker-compose logs -f api-gateway
docker-compose logs -f user-service
docker-compose logs -f ui-service
```

#### Individual Services (for development)
```bash
# Backend services
poetry run uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
poetry run uvicorn services.user.main:app --host 0.0.0.0 --port 8003 --reload
poetry run uvicorn services.inventory.main:app --host 0.0.0.0 --port 8001 --reload
poetry run uvicorn services.location.main:app --host 0.0.0.0 --port 8002 --reload
poetry run uvicorn services.reporting.main:app --host 0.0.0.0 --port 8004 --reload

# Frontend (React development server)
cd services/ui
npm start
```

### Testing

#### Run All Tests
```bash
# Run all tests with coverage
poetry run pytest --cov=services --cov=shared --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### Test Categories
```bash
# Unit tests (fast, isolated)
poetry run pytest tests/unit/

# Integration tests (slower, with database)
poetry run pytest tests/integration/

# Property-based tests (comprehensive, randomized)
poetry run pytest tests/property/

# Specific test file
poetry run pytest tests/unit/test_authentication_edge_cases.py -v
```

### Code Quality

#### Formatting and Linting
```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8

# Type checking
poetry run mypy services/ shared/
```

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

## 📁 Project Structure

```
inventory-management-system/
├── .github/                   # GitHub Actions workflows
│   └── workflows/             # CI/CD pipeline definitions
├── .kiro/                     # Kiro AI specifications
│   └── specs/                 # Feature specifications and requirements
├── services/                  # Microservices
│   ├── api_gateway/          # API Gateway Service (routing, auth)
│   ├── user/                 # User Service (auth, users, roles)
│   ├── inventory/            # Inventory Service (items, relationships) [WIP]
│   ├── location/             # Location Service (locations, movements) [WIP]
│   ├── reporting/            # Reporting Service (analytics) [WIP]
│   └── ui/                   # React UI Service
│       ├── src/              # React source code
│       ├── public/           # Static assets
│       ├── Dockerfile        # UI container configuration
│       └── nginx.conf        # Nginx configuration
├── shared/                   # Shared utilities and models
│   ├── auth/                 # Authentication utilities (JWT, bcrypt)
│   ├── config/               # Configuration management
│   ├── database/             # Database utilities and connections
│   ├── logging/              # Structured logging configuration
│   └── models/               # SQLAlchemy data models
├── tests/                    # Comprehensive test suites
│   ├── unit/                 # Unit tests (fast, isolated)
│   ├── integration/          # Integration tests (with database)
│   ├── property/             # Property-based tests (Hypothesis)
│   └── conftest.py           # Pytest configuration and fixtures
├── terraform/                # Infrastructure as Code
│   ├── environments/         # Environment-specific configurations
│   │   ├── dev/              # Development environment
│   │   └── prod/             # Production environment
│   └── modules/              # Reusable Terraform modules
│       ├── networking/       # VPC, subnets, security groups
│       ├── ecs-cluster/      # ECS Fargate cluster
│       ├── ecs-service/      # ECS service definitions
│       ├── alb/              # Application Load Balancer
│       ├── rds/              # PostgreSQL database
│       └── elasticache/      # Redis cache
├── scripts/                  # Utility scripts
│   ├── create_admin_user.py  # Admin user creation
│   ├── deploy.sh             # Deployment automation
│   └── health-check.sh       # Health check utilities
├── migrations/               # Database migrations (Alembic)
├── docker/                   # Docker configurations
├── docs/                     # Additional documentation
├── docker-compose.yml        # Local development environment
├── docker-compose.prod.yml   # Production-like environment
├── pyproject.toml           # Python project configuration
├── alembic.ini              # Database migration configuration
└── README.md                # This file
```

## 📚 API Documentation

### Interactive API Documentation
Once the services are running, access the interactive API documentation:

- **API Gateway**: http://localhost:8000/docs (or live: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/docs)
- **User Service**: http://localhost:8003/docs
- **Inventory Service**: http://localhost:8001/docs
- **Location Service**: http://localhost:8002/docs
- **Reporting Service**: http://localhost:8004/docs

### Key API Endpoints

#### Authentication
```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin"
}

# Get current user
GET /api/v1/auth/me
Authorization: Bearer <token>

# Refresh token
POST /api/v1/auth/refresh
Authorization: Bearer <token>
```

#### User Management
```bash
# List users
GET /api/v1/users/
Authorization: Bearer <token>

# Create user
POST /api/v1/users/
Authorization: Bearer <token>
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "role_id": "<role-uuid>"
}
```

## 🔍 Monitoring and Logging

### Health Checks
Each service provides comprehensive health check endpoints:

- **Basic Health**: `GET /health` - Service availability
- **Readiness Check**: `GET /health/ready` - Database connectivity and dependencies
- **Detailed Status**: `GET /health/detailed` - Component-level health information

### Logging
The system uses structured JSON logging compatible with CloudWatch and other log aggregation systems:

```bash
# View service logs
docker-compose logs -f api-gateway
docker-compose logs -f user-service

# Follow all logs
docker-compose logs -f
```

### Metrics and Observability
- **Request/Response logging** with correlation IDs
- **Performance metrics** for database queries
- **Error tracking** with stack traces
- **Authentication audit logs**

## 🚀 Deployment

### AWS Infrastructure
The system is deployed on AWS using Terraform for Infrastructure as Code:

#### Current Deployment
- **Environment**: Development
- **URL**: http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/
- **Region**: us-west-2
- **Compute**: AWS Fargate (serverless containers)
- **Database**: Amazon RDS PostgreSQL
- **Cache**: Amazon ElastiCache Redis
- **Load Balancer**: Application Load Balancer

#### Infrastructure Components
```bash
# Deploy infrastructure
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Update services
./scripts/deploy.sh
```

### CI/CD Pipeline
GitHub Actions automatically:
1. **Tests**: Run unit, integration, and property-based tests
2. **Quality**: Code formatting, linting, and type checking
3. **Security**: Dependency vulnerability scanning
4. **Build**: Create Docker images for all services
5. **Deploy**: Push to ECR and update ECS services

### Environment Configuration

#### Development
- Local Docker Compose setup
- SQLite/PostgreSQL database
- Hot reloading for development

#### Production
- AWS Fargate with auto-scaling
- RDS PostgreSQL with backups
- ElastiCache Redis cluster
- CloudWatch logging and monitoring

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests (`tests/unit/`)
- **Fast execution** (< 1 second per test)
- **Isolated** (no external dependencies)
- **High coverage** of business logic
- **Mocked dependencies**

#### Integration Tests (`tests/integration/`)
- **Real database** connections
- **Service-to-service** communication
- **End-to-end workflows**
- **Performance testing**

#### Property-Based Tests (`tests/property/`)
- **Hypothesis-driven** testing
- **Randomized inputs** for comprehensive coverage
- **Invariant checking** (properties that should always hold)
- **Edge case discovery**

### Test Execution
```bash
# Run all tests with coverage
poetry run pytest --cov=services --cov=shared --cov-report=html

# Run specific test categories
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
poetry run pytest tests/property/ -v

# Run tests in parallel (faster)
poetry run pytest -n auto

# Run with specific markers
poetry run pytest -m "not slow"
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Process
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** the existing code style and patterns
4. **Write tests** for new functionality
5. **Update documentation** as needed
6. **Ensure all tests pass** (`poetry run pytest`)
7. **Run code quality checks** (`poetry run black . && poetry run flake8`)
8. **Commit** your changes (`git commit -m 'Add amazing feature'`)
9. **Push** to the branch (`git push origin feature/amazing-feature`)
10. **Open** a Pull Request

### Code Standards
- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Follow ESLint rules, use Prettier for formatting
- **Testing**: Maintain >90% code coverage
- **Documentation**: Update README and inline docs
- **Commits**: Use conventional commit messages

### Development Setup for Contributors
```bash
# Clone your fork
git clone https://github.com/yourusername/inventory-management-system.git
cd inventory-management-system

# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Run tests to ensure everything works
poetry run pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: [GitHub Issues](https://github.com/yourusername/inventory-management-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/inventory-management-system/discussions)
- **Documentation**: Check this README and inline code documentation

### Reporting Bugs
When reporting bugs, please include:
1. **Environment details** (OS, Python version, etc.)
2. **Steps to reproduce** the issue
3. **Expected vs actual behavior**
4. **Error messages** and stack traces
5. **Relevant logs** from the application

### Feature Requests
For feature requests, please:
1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and business value
3. **Provide examples** of how it would work
4. **Consider implementation complexity**

## 🗺️ Roadmap

### Phase 1: Foundation ✅
- [x] Microservices architecture
- [x] User authentication and authorization
- [x] React UI with Material-UI
- [x] AWS deployment with Terraform
- [x] CI/CD pipeline
- [x] Comprehensive testing framework

### Phase 2: Core Inventory (In Progress) 🚧
- [ ] Parent/child item management
- [ ] Item type definitions and validation
- [ ] Basic inventory operations (add, update, delete)
- [ ] Item search and filtering

### Phase 3: Location Management 🔄
- [ ] Multi-level location hierarchy
- [ ] Item movement tracking
- [ ] Location-based inventory views
- [ ] Movement history and audit trail

### Phase 4: Advanced Features 📋
- [ ] Real-time dashboards and reporting
- [ ] Advanced search and filtering
- [ ] Bulk operations and imports
- [ ] API rate limiting and caching
- [ ] Mobile-responsive UI improvements

### Phase 5: Enterprise Features 🎯
- [ ] Multi-tenant support
- [ ] Advanced role-based permissions
- [ ] Integration APIs (REST/GraphQL)
- [ ] Automated backup and disaster recovery
- [ ] Performance optimization and scaling

---

## 🏆 Acknowledgments

- **FastAPI** for the excellent Python web framework
- **React** and **Material-UI** for the frontend components
- **AWS** for reliable cloud infrastructure
- **Terraform** for infrastructure as code
- **GitHub Actions** for CI/CD automation
- **Hypothesis** for property-based testing framework

---

**Built with ❤️ by the development team**