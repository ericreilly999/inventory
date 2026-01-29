# Database Migration Strategy

This document explains how database migrations are managed in the Inventory Management System.

## Overview

We use **Alembic** for database migrations. Alembic provides:
- Version control for database schema changes
- Automatic tracking of applied migrations
- Safe, idempotent migration execution
- Rollback capabilities

## How Alembic Tracks Migrations

### Version Tracking
- Alembic creates a table called `alembic_version` in your database
- This table stores the current migration revision ID
- When you run `alembic upgrade head`, it:
  1. Checks `alembic_version` to see what's currently applied
  2. Compares with available migration files in `migrations/versions/`
  3. **Only runs migrations that haven't been applied yet**
  4. Updates `alembic_version` after each successful migration

### Idempotency
- Running migrations multiple times is **safe**
- Already-applied migrations are automatically skipped
- No risk of duplicate schema changes

## Migration Execution Strategy

### Production Approach: ECS Task

Migrations run as a **dedicated ECS Fargate task** before deployments:

**Why ECS Task?**
- ✅ Runs inside the VPC (can reach private RDS database)
- ✅ Uses same network configuration as application services
- ✅ Automatic credential management via AWS Secrets Manager
- ✅ CloudWatch logs for debugging
- ✅ Isolated from application containers
- ✅ Can run before deployment to ensure schema is ready

**Why NOT GitHub Actions Runner?**
- ❌ Runs outside VPC (cannot reach private RDS)
- ❌ Would require public database access (security risk)
- ❌ Requires managing database credentials in GitHub

### Migration Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    CD Pipeline Triggered                     │
│                  (Push to main or manual)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Build & Push Docker Images to ECR               │
│        (api-gateway, inventory, location, user, etc.)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Run Database Migration ECS Task                 │
│                                                               │
│  1. Get network config from existing service                 │
│  2. Run migration task in same VPC/subnet                    │
│  3. Task executes: alembic upgrade head                      │
│  4. Alembic checks alembic_version table                     │
│  5. Runs only new migrations                                 │
│  6. Updates alembic_version                                  │
│  7. Task exits with success/failure code                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                    Migration
                    Successful?
                         │
                ┌────────┴────────┐
                │                 │
               Yes               No
                │                 │
                ▼                 ▼
    ┌───────────────────┐  ┌──────────────┐
    │ Deploy Services   │  │ Stop Pipeline│
    │ to ECS            │  │ Report Error │
    └───────────────────┘  └──────────────┘
```

## Creating New Migrations

### 1. Auto-generate from Model Changes

```bash
# After modifying models in shared/models/
alembic revision --autogenerate -m "description of changes"
```

This creates a new migration file in `migrations/versions/` with:
- Unique revision ID
- Reference to previous revision
- Auto-detected schema changes

### 2. Manual Migration

```bash
# For complex changes or data migrations
alembic revision -m "description of changes"
```

Then edit the generated file to add custom logic.

### 3. Review the Migration

Always review auto-generated migrations:
- Check the `upgrade()` function
- Verify the `downgrade()` function
- Test locally before committing

## Running Migrations

### Automatic (Production)

Migrations run automatically during CD pipeline:
1. Code is pushed to `main` branch
2. Docker images are built
3. Migration ECS task runs
4. Services are deployed with new code

### Manual (Development)

#### Local Development

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

# Run migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

#### Via ECS Task (Production/Staging)

```bash
# Run the migration script
./run_migration_ecs.sh dev us-west-2

# Or manually
aws ecs run-task \
  --cluster dev-inventory-cluster \
  --task-definition dev-migration-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --region us-west-2
```

## Migration Task Configuration

### Terraform Module

The migration task is defined in `terraform/modules/migration-task/`:

```hcl
module "migration_task" {
  source = "../../modules/migration-task"
  
  environment          = "dev"
  aws_region          = "us-west-2"
  migration_image     = "290993374431.dkr.ecr.us-west-2.amazonaws.com/inventory-management/inventory-service:latest"
  database_secret_arn = aws_secretsmanager_secret.database.arn
  
  tags = local.common_tags
}
```

### Task Definition

- **CPU**: 256 (0.25 vCPU)
- **Memory**: 512 MB
- **Network**: Same VPC/subnet as application services
- **Credentials**: Loaded from AWS Secrets Manager
- **Logs**: CloudWatch Logs at `/ecs/{environment}/migration-task`

### Container Command

```bash
sh -c "pip install --no-cache-dir alembic psycopg2-binary sqlalchemy pydantic pydantic-settings python-dotenv && alembic upgrade head"
```

## Troubleshooting

### Migration Fails in Pipeline

1. **Check CloudWatch Logs**:
   ```
   AWS Console → CloudWatch → Log Groups → /ecs/dev/migration-task
   ```

2. **Common Issues**:
   - **Database credentials incorrect**: Check Secrets Manager
   - **Network connectivity**: Verify security group allows traffic
   - **Migration syntax error**: Test migration locally first
   - **Conflicting migrations**: Check migration history

### View Current Database Version

```bash
# Connect to database
psql $DATABASE_URL

# Check version
SELECT * FROM alembic_version;
```

### Manually Fix Migration State

If migrations get out of sync:

```bash
# Mark a specific version as current (without running it)
alembic stamp <revision_id>

# Example: Mark as head
alembic stamp head
```

### Rollback a Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Best Practices

### 1. Test Migrations Locally First

```bash
# Create test database
createdb inventory_test

# Run migration
DATABASE_URL="postgresql://localhost/inventory_test" alembic upgrade head

# Verify schema
psql inventory_test -c "\dt"

# Test rollback
DATABASE_URL="postgresql://localhost/inventory_test" alembic downgrade -1
```

### 2. Keep Migrations Small

- One logical change per migration
- Easier to review and rollback
- Faster execution

### 3. Always Provide Downgrade

- Every `upgrade()` should have a corresponding `downgrade()`
- Enables safe rollbacks
- Required for production systems

### 4. Avoid Data Loss

- Use `ALTER COLUMN` carefully
- Back up data before destructive changes
- Consider two-phase migrations for column renames:
  1. Add new column, copy data
  2. Remove old column (separate migration)

### 5. Handle Existing Data

```python
def upgrade():
    # Add column with default
    op.add_column('users', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
    
    # Remove server default after backfill
    op.alter_column('users', 'status', server_default=None)

def downgrade():
    op.drop_column('users', 'status')
```

## Migration File Structure

```python
"""description of changes

Revision ID: 49871d03964c
Revises: 48871d03964b
Create Date: 2026-01-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "49871d03964c"
down_revision = "48871d03964b"
branch_labels = None
depends_on = None

def upgrade():
    """Apply schema changes."""
    op.alter_column("parent_items", "name", new_column_name="sku")
    op.alter_column("child_items", "name", new_column_name="sku")

def downgrade():
    """Revert schema changes."""
    op.alter_column("parent_items", "sku", new_column_name="name")
    op.alter_column("child_items", "sku", new_column_name="name")
```

## Security Considerations

### Database Credentials

- ✅ Stored in AWS Secrets Manager
- ✅ Automatically rotated
- ✅ Accessed via IAM roles (no hardcoded credentials)
- ✅ Encrypted at rest and in transit

### Network Security

- ✅ RDS in private subnet (no public access)
- ✅ Security groups restrict access to ECS tasks only
- ✅ Migration task runs in same VPC as application

### Audit Trail

- ✅ All migrations logged to CloudWatch
- ✅ Git history tracks migration files
- ✅ `alembic_version` table shows current state

## Monitoring

### CloudWatch Metrics

Monitor migration task execution:
- Task start/stop events
- Exit codes
- Duration
- Errors

### Alerts

Set up CloudWatch alarms for:
- Migration task failures
- Long-running migrations (> 5 minutes)
- Repeated failures

## FAQ

**Q: What happens if a migration fails mid-execution?**
A: Alembic runs each migration in a transaction. If it fails, the transaction is rolled back and the database remains in the previous state.

**Q: Can I run migrations while the application is running?**
A: Yes, but be careful with:
- Column drops (application may still reference them)
- Column renames (use two-phase approach)
- Index creation (can lock tables)

**Q: How do I handle migrations across multiple environments?**
A: Each environment has its own `alembic_version` table. Migrations are applied independently to each environment.

**Q: What if two developers create migrations at the same time?**
A: Alembic will detect the conflict. Use `alembic merge` to create a merge migration that references both branches.

**Q: Can I skip a migration?**
A: Not recommended. If you must, use `alembic stamp` to mark it as applied without running it.

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [AWS ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
