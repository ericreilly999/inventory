# Database Migration Strategy - Implementation Summary

## Problem Statement

The application needed to rename the `name` column to `sku` in both `parent_items` and `child_items` tables. However, running migrations from the GitHub Actions runner failed because:

1. **Network Isolation**: RDS database is in a private subnet (10.0.20.233)
2. **No Public Access**: Database is not publicly accessible (security best practice)
3. **GitHub Runner Location**: Runs outside the VPC, cannot reach private resources

## Solution: ECS Task-Based Migrations

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    GitHub Actions Runner                      │
│                   (Outside VPC - Public)                      │
│                                                                │
│  1. Build Docker images                                       │
│  2. Push to ECR                                               │
│  3. Trigger ECS migration task ──────────┐                   │
│  4. Wait for completion                   │                   │
│  5. Deploy services                       │                   │
└───────────────────────────────────────────┼───────────────────┘
                                            │
                                            │ AWS API Call
                                            │
                                            ▼
┌──────────────────────────────────────────────────────────────┐
│                         AWS VPC                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           ECS Migration Task (Fargate)                 │  │
│  │                                                         │  │
│  │  - Runs in private subnet                              │  │
│  │  - Has network access to RDS                           │  │
│  │  - Loads DATABASE_URL from Secrets Manager             │  │
│  │  - Executes: alembic upgrade head                      │  │
│  │  - Logs to CloudWatch                                  │  │
│  └────────────────────┬───────────────────────────────────┘  │
│                       │                                       │
│                       │ Database Connection                   │
│                       ▼                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              RDS PostgreSQL (Private)                  │  │
│  │                                                         │  │
│  │  - Checks alembic_version table                        │  │
│  │  - Runs pending migrations                             │  │
│  │  - Updates alembic_version                             │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Terraform Module (`terraform/modules/migration-task/`)

Defines the ECS task definition for running migrations:

- **Task Definition**: `{environment}-migration-task`
- **CPU/Memory**: 256 CPU / 512 MB (minimal resources)
- **Network**: Same VPC/subnet as application services
- **Image**: Uses inventory-service image (contains alembic.ini and migrations/)
- **Command**: Installs dependencies and runs `alembic upgrade head`
- **Credentials**: Loaded from AWS Secrets Manager
- **Logs**: CloudWatch at `/ecs/{environment}/migration-task`

#### 2. CD Pipeline Integration (`.github/workflows/cd.yml`)

Migration step runs before service deployment:

```yaml
- name: Run database migrations via ECS task
  run: |
    # Get network configuration from existing service
    SERVICE_INFO=$(aws ecs describe-services ...)
    
    # Run migration task in same VPC
    TASK_ARN=$(aws ecs run-task \
      --task-definition dev-migration-task \
      --network-configuration "..." \
      ...)
    
    # Wait for completion
    aws ecs wait tasks-stopped ...
    
    # Check exit code
    if [ "$EXIT_CODE" != "0" ]; then
      exit 1
    fi
```

#### 3. Manual Migration Script (`run_migration_ecs.sh`)

For manual migration execution:

```bash
./run_migration_ecs.sh dev us-west-2
```

Features:
- Gets network config from existing services
- Runs task in correct VPC/subnet
- Waits for completion
- Reports success/failure
- Provides CloudWatch log link

### How Alembic Tracks Migrations

#### Version Table

Alembic creates and maintains an `alembic_version` table:

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

Current state:
```sql
SELECT * FROM alembic_version;
-- version_num
-- 48871d03964b  (before our migration)
```

After migration:
```sql
SELECT * FROM alembic_version;
-- version_num
-- 49871d03964c  (our migration applied)
```

#### Migration Execution Flow

1. **Check Current Version**:
   ```python
   current = db.query(alembic_version).scalar()  # "48871d03964b"
   ```

2. **Find Pending Migrations**:
   ```python
   # Scans migrations/versions/ directory
   # Finds: 49871d03964c_rename_name_to_sku.py
   # Checks: down_revision = "48871d03964b" (matches current)
   ```

3. **Run Migration**:
   ```python
   # Execute upgrade() function
   op.alter_column("parent_items", "name", new_column_name="sku")
   op.alter_column("child_items", "name", new_column_name="sku")
   ```

4. **Update Version**:
   ```sql
   UPDATE alembic_version SET version_num = '49871d03964c';
   ```

#### Idempotency

Running migrations multiple times is safe:

```bash
# First run
alembic upgrade head
# → Runs migration 49871d03964c
# → Updates alembic_version to 49871d03964c

# Second run
alembic upgrade head
# → Checks alembic_version: 49871d03964c
# → No pending migrations
# → Does nothing (exits successfully)
```

## Implementation Details

### Files Created/Modified

#### New Files

1. **terraform/modules/migration-task/main.tf**
   - ECS task definition
   - IAM roles and policies
   - CloudWatch log group

2. **terraform/modules/migration-task/variables.tf**
   - Module input variables

3. **terraform/modules/migration-task/outputs.tf**
   - Task definition ARN and family
   - Log group name

4. **docs/DATABASE_MIGRATIONS.md**
   - Comprehensive migration documentation
   - Best practices and troubleshooting

5. **MIGRATION_QUICK_START.md**
   - Quick reference guide
   - Common commands

#### Modified Files

1. **.github/workflows/cd.yml**
   - Removed direct migration execution (can't reach database)
   - Added ECS task-based migration step
   - Runs before service deployment

2. **run_migration_ecs.sh**
   - Improved error handling
   - Better logging and output
   - CloudWatch log links

3. **Test Files** (32 files updated)
   - Changed `name=` to `sku=` for ParentItem/ChildItem
   - Updated assertions to check `sku` instead of `name`

### Migration File

**migrations/versions/49871d03964c_rename_name_to_sku.py**

```python
def upgrade():
    """Rename name column to sku in parent_items and child_items tables."""
    op.alter_column("parent_items", "name", new_column_name="sku")
    op.alter_column("child_items", "name", new_column_name="sku")

def downgrade():
    """Revert sku column back to name."""
    op.alter_column("parent_items", "sku", new_column_name="name")
    op.alter_column("child_items", "sku", new_column_name="name")
```

## Deployment Workflow

### Automatic (Production)

1. **Developer pushes to main**
   ```bash
   git push origin main
   ```

2. **CI Pipeline runs** (Quality Assurance)
   - Linting, formatting, type checking
   - Unit tests, integration tests
   - Property-based tests
   - Coverage reports

3. **CD Pipeline runs** (Continuous Deployment)
   - Build Docker images for all services
   - Push images to ECR
   - **Run migration ECS task** ← NEW STEP
   - Deploy services to ECS
   - Wait for services to stabilize
   - Verify deployment

4. **Migration Task Execution**
   - Task starts in private subnet
   - Connects to RDS database
   - Runs `alembic upgrade head`
   - Alembic checks `alembic_version` table
   - Runs only new migrations
   - Updates `alembic_version`
   - Task exits with success/failure

5. **Service Deployment**
   - Only proceeds if migration succeeds
   - Services start with updated code
   - Code expects `sku` column (which now exists)

### Manual (Development/Troubleshooting)

```bash
# Run migration manually
./run_migration_ecs.sh dev us-west-2

# Or via AWS CLI
aws ecs run-task \
  --cluster dev-inventory-cluster \
  --task-definition dev-migration-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={...}"

# View logs
aws logs tail /ecs/dev/migration-task --follow
```

## Security Considerations

### Database Credentials

✅ **Stored in AWS Secrets Manager**
- Encrypted at rest
- Automatic rotation supported
- Access controlled via IAM

✅ **No Hardcoded Credentials**
- Not in code
- Not in environment variables (GitHub)
- Loaded at runtime via IAM role

### Network Security

✅ **Private Subnet**
- RDS not publicly accessible
- No internet-facing endpoints

✅ **Security Groups**
- Only ECS tasks can connect
- Port 5432 restricted to VPC

✅ **VPC Isolation**
- Migration task runs in same VPC
- Uses private networking

### Audit Trail

✅ **CloudWatch Logs**
- All migration output logged
- Searchable and filterable
- Retention policy enforced

✅ **Git History**
- Migration files version controlled
- Code review required
- Audit trail of changes

✅ **Database Version Table**
- `alembic_version` shows current state
- Immutable history

## Monitoring and Troubleshooting

### CloudWatch Logs

View migration logs:
```
AWS Console → CloudWatch → Log Groups → /ecs/dev/migration-task
```

Or via CLI:
```bash
aws logs tail /ecs/dev/migration-task --follow
```

### Common Issues

#### 1. Migration Task Fails to Start

**Symptoms**: Task never starts or fails immediately

**Causes**:
- Task definition not found
- Network configuration incorrect
- IAM permissions missing

**Solution**:
```bash
# Check task definition exists
aws ecs describe-task-definition --task-definition dev-migration-task

# Check IAM role permissions
aws iam get-role --role-name dev-migration-task-execution-role
```

#### 2. Database Connection Timeout

**Symptoms**: Task starts but can't connect to database

**Causes**:
- Security group doesn't allow traffic
- Wrong subnet (not in VPC)
- Database credentials incorrect

**Solution**:
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxx

# Verify database secret
aws secretsmanager get-secret-value --secret-id dev/inventory-management/database
```

#### 3. Migration SQL Error

**Symptoms**: Task connects but migration fails

**Causes**:
- Migration script error
- Database schema conflict
- Data incompatibility

**Solution**:
```bash
# Check CloudWatch logs for SQL error
aws logs tail /ecs/dev/migration-task --since 10m

# Connect to database and check manually
psql $DATABASE_URL
\d parent_items  -- Check table structure
```

#### 4. Migrations Out of Sync

**Symptoms**: Alembic reports version mismatch

**Causes**:
- Manual database changes
- Failed migration left partial state
- Multiple environments out of sync

**Solution**:
```bash
# Check current version
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# Stamp to specific version (without running migration)
alembic stamp 49871d03964c

# Or reset to head
alembic stamp head
```

### Health Checks

#### Before Deployment

```bash
# Check current database version
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# Check pending migrations
alembic current
alembic history --verbose
```

#### After Deployment

```bash
# Verify migration ran
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
# Should show: 49871d03964c

# Verify column renamed
psql $DATABASE_URL -c "\d parent_items"
# Should show: sku column (not name)

# Check application logs
aws logs tail /ecs/dev/inventory-service --follow
```

## Benefits of This Approach

### ✅ Security
- Database remains private
- No public access required
- Credentials managed securely

### ✅ Reliability
- Migrations run before deployment
- Automatic rollback on failure
- Idempotent execution

### ✅ Visibility
- CloudWatch logs for debugging
- Pipeline integration
- Clear success/failure reporting

### ✅ Consistency
- Same process for all environments
- Automated and repeatable
- Version controlled

### ✅ Maintainability
- Terraform-managed infrastructure
- Self-documenting code
- Easy to extend

## Future Enhancements

### 1. Blue/Green Deployments

Run migrations during blue/green cutover:
- Deploy new version (blue)
- Run migrations
- Switch traffic to blue
- Decommission green

### 2. Migration Rollback Automation

Automatically rollback on deployment failure:
```yaml
- name: Rollback migration on failure
  if: failure()
  run: alembic downgrade -1
```

### 3. Multi-Environment Support

Extend to staging and production:
```hcl
module "migration_task_staging" {
  source = "../../modules/migration-task"
  environment = "staging"
  ...
}

module "migration_task_prod" {
  source = "../../modules/migration-task"
  environment = "prod"
  ...
}
```

### 4. Migration Testing

Add migration testing to CI:
```yaml
- name: Test migrations
  run: |
    # Create test database
    createdb test_db
    
    # Run migrations
    DATABASE_URL="postgresql://localhost/test_db" alembic upgrade head
    
    # Verify schema
    psql test_db -c "\d parent_items"
    
    # Test rollback
    DATABASE_URL="postgresql://localhost/test_db" alembic downgrade -1
```

## Conclusion

The ECS task-based migration strategy provides a secure, reliable, and maintainable approach to database schema changes. By running migrations from within the VPC, we maintain security best practices while enabling automated deployments.

**Key Takeaways**:
1. Alembic automatically tracks and manages migration state
2. Running migrations multiple times is safe (idempotent)
3. ECS tasks provide VPC access for private databases
4. Migrations run before deployment to ensure schema readiness
5. CloudWatch logs provide visibility and debugging capability

## Resources

- [Full Documentation](docs/DATABASE_MIGRATIONS.md)
- [Quick Start Guide](MIGRATION_QUICK_START.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [AWS ECS Task Definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html)
