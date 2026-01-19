"""Test project structure and basic imports."""

import pytest
from pathlib import Path


def test_project_structure():
    """Test that all required directories exist."""
    base_path = Path(".")
    
    # Check main directories
    assert (base_path / "services").exists()
    assert (base_path / "shared").exists()
    assert (base_path / "tests").exists()
    
    # Check service directories
    services = ["api_gateway", "inventory", "location", "user", "reporting", "ui"]
    for service in services:
        assert (base_path / "services" / service).exists()
        assert (base_path / "services" / service / "__init__.py").exists()
    
    # Check shared directories
    shared_modules = ["auth", "config", "database", "logging", "health"]
    for module in shared_modules:
        assert (base_path / "shared" / module).exists()
        assert (base_path / "shared" / module / "__init__.py").exists()


def test_config_imports():
    """Test that configuration modules can be imported."""
    from shared.config.settings import settings
    from shared.logging.config import configure_logging, get_logger
    from shared.database.config import Base, get_db
    from shared.auth.utils import hash_password, verify_password
    
    # Basic assertions
    assert settings is not None
    assert settings.environment == "development"
    assert callable(configure_logging)
    assert callable(get_logger)
    assert Base is not None
    assert callable(get_db)
    assert callable(hash_password)
    assert callable(verify_password)


def test_docker_files_exist():
    """Test that Docker configuration files exist."""
    base_path = Path(".")
    
    # Check Docker Compose
    assert (base_path / "docker-compose.yml").exists()
    
    # Check service Dockerfiles
    services = ["api_gateway", "inventory", "location", "user", "reporting", "ui"]
    for service in services:
        dockerfile_path = base_path / "services" / service / "Dockerfile"
        assert dockerfile_path.exists(), f"Dockerfile missing for {service}"


def test_development_files_exist():
    """Test that development configuration files exist."""
    base_path = Path(".")
    
    required_files = [
        "pyproject.toml",
        "README.md",
        "Makefile",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".env.example",
        "alembic.ini"
    ]
    
    for file_name in required_files:
        assert (base_path / file_name).exists(), f"{file_name} is missing"