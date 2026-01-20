# Local values for environment-specific configuration

locals {
  # Environment-specific tags
  environment_tags = {
    dev = {
      Environment = "development"
      Product     = "inventory-management"
      ManagedBy   = "terraform"
      Owner       = "development-team"
      CostCenter  = "engineering"
      Backup      = "daily"
    }

    staging = {
      Environment = "staging"
      Product     = "inventory-management"
      ManagedBy   = "terraform"
      Owner       = "qa-team"
      CostCenter  = "engineering"
      Backup      = "daily"
    }

    prod = {
      Environment = "production"
      Product     = "inventory-management"
      ManagedBy   = "terraform"
      Owner       = "platform-team"
      CostCenter  = "operations"
      Backup      = "hourly"
      Compliance  = "required"
    }
  }

  # Environment-specific resource sizing
  resource_sizing = {
    dev = {
      db_instance_class = "db.t3.micro"
      cache_node_type   = "cache.t3.micro"
      container_cpu     = 256
      container_memory  = 512
      min_capacity      = 1
      max_capacity      = 3
    }

    staging = {
      db_instance_class = "db.t3.small"
      cache_node_type   = "cache.t3.small"
      container_cpu     = 256
      container_memory  = 512
      min_capacity      = 1
      max_capacity      = 5
    }

    prod = {
      db_instance_class = "db.r6g.large"
      cache_node_type   = "cache.r6g.large"
      container_cpu     = 512
      container_memory  = 1024
      min_capacity      = 2
      max_capacity      = 20
    }
  }

  # Environment-specific security settings
  security_settings = {
    dev = {
      deletion_protection   = false
      backup_retention_days = 7
      multi_az              = false
      encryption_enabled    = true
    }

    staging = {
      deletion_protection   = false
      backup_retention_days = 7
      multi_az              = true
      encryption_enabled    = true
    }

    prod = {
      deletion_protection   = true
      backup_retention_days = 30
      multi_az              = true
      encryption_enabled    = true
    }
  }

  # Environment-specific monitoring settings
  monitoring_settings = {
    dev = {
      log_retention_days   = 7
      detailed_monitoring  = false
      performance_insights = false
      container_insights   = false
    }

    staging = {
      log_retention_days   = 14
      detailed_monitoring  = true
      performance_insights = true
      container_insights   = true
    }

    prod = {
      log_retention_days   = 30
      detailed_monitoring  = true
      performance_insights = true
      container_insights   = true
    }
  }
}