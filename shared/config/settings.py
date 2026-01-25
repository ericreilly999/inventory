"""Configuration settings for the inventory management system."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")

    # Database settings
    database_url: str = Field(
        default=(
            "postgresql://inventory_user:inventory_password@"
            "localhost:5432/inventory_management"
        ),
        env="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_decode_responses: bool = Field(default=True, env="REDIS_DECODE_RESPONSES")
    redis_socket_connect_timeout: int = Field(
        default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT"
    )
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")

    # Auth settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production", env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    password_hash_rounds: int = Field(default=12, env="PASSWORD_HASH_ROUNDS")

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    service_name: str = Field(default="inventory-service", env="SERVICE_NAME")

    # Monitoring settings
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    health_check_timeout: int = Field(default=30, env="HEALTH_CHECK_TIMEOUT")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")

    # API settings
    api_title: str = Field(default="Inventory Management API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_description: str = Field(
        default="Microservices-based inventory management system",
        env="API_DESCRIPTION",
    )
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8005",
            "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
            "https://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com",
        ],
        env="CORS_ORIGINS",
    )
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    class Config:
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database(self):
        """Database settings for backward compatibility."""

        class DatabaseSettings:
            def __init__(self, settings_instance):
                self.url = settings_instance.database_url
                self.echo = settings_instance.database_echo
                self.pool_size = settings_instance.database_pool_size
                self.max_overflow = settings_instance.database_max_overflow

        return DatabaseSettings(self)

    @property
    def redis(self):
        """Redis settings for backward compatibility."""

        class RedisSettings:
            def __init__(self, settings_instance):
                self.url = settings_instance.redis_url
                self.decode_responses = settings_instance.redis_decode_responses
                self.socket_connect_timeout = (
                    settings_instance.redis_socket_connect_timeout
                )
                self.socket_timeout = settings_instance.redis_socket_timeout

        return RedisSettings(self)

    @property
    def auth(self):
        """Auth settings for backward compatibility."""

        class AuthSettings:
            def __init__(self, settings_instance):
                self.jwt_secret_key = settings_instance.jwt_secret_key
                self.jwt_algorithm = settings_instance.jwt_algorithm
                self.jwt_expiration_hours = settings_instance.jwt_expiration_hours
                self.password_hash_rounds = settings_instance.password_hash_rounds

        return AuthSettings(self)

    @property
    def logging(self):
        """Logging settings for backward compatibility."""

        class LoggingSettings:
            def __init__(self, settings_instance):
                self.level = settings_instance.log_level
                self.format = settings_instance.log_format
                self.service_name = settings_instance.service_name

        return LoggingSettings(self)

    @property
    def monitoring(self):
        """Monitoring settings for backward compatibility."""

        class MonitoringSettings:
            def __init__(self, settings_instance):
                self.prometheus_port = settings_instance.prometheus_port
                self.health_check_timeout = settings_instance.health_check_timeout
                self.metrics_enabled = settings_instance.metrics_enabled

        return MonitoringSettings(self)

    @property
    def api(self):
        """API settings for backward compatibility."""

        class APISettings:
            def __init__(self, settings_instance):
                self.title = settings_instance.api_title
                self.version = settings_instance.api_version
                self.description = settings_instance.api_description
                self.cors_origins = settings_instance.cors_origins
                self.rate_limit_requests = settings_instance.rate_limit_requests
                self.rate_limit_window = settings_instance.rate_limit_window

        return APISettings(self)


# Global settings instance
settings = Settings()
