# Database Migration Quick Start

## TL;DR

**Migrations run automatically** when you push to `main`. They execute via ECS task before deployment.

## For Developers

### Create a New Migration

```bash
# After changing models in shared/models/
alembic revision --autogenerate -m "add user preferences table"

# Review the generated file in migrations/versions/
# Commit and push to trigger deployment
```

### Test Locally

```bash
export DATABASE_URL="postgresql://localhost/inventory_test"
alembic upgrade head
```

### Check Migration Status

```bash
# Current version
alembic current

# History
alembic history --verbose

# Pending migrations
alembic upgrade head --sql  # Shows SQL without executing
```

## For DevOps

### Run Migration Manually (Production)

```bash
# Via script
./run_migration_ecs.sh dev us-west-2

# Or via AWS CLI
aws ecs run-task \
  --cluster dev-inventory-cluster \
  --task-definition dev-migration-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"
```

### View Migration Logs

```
AWS Console → CloudWatch → Log Groups → /ecs/dev/migration-task
```

### Check Database Version

```sql
-- Connect to database
psql $DATABASE_URL

-- Check current version
SELECT * FROM alembic_version;
```

## How It Works

1. **Push to main** → Triggers CD pipeline
2. **Build images** → Docker images pushed to ECR
3. **Run migration task** → ECS task executes `alembic upgrade head`
4. **Alembic checks** → Reads `alembic_version` table
5. **Runs new migrations** → Only migrations not yet applied
6. **Updates version** → Records new version in database
7. **Deploy services** → Application services updated

## Key Points

✅ **Idempotent**: Safe to run multiple times
✅ **Automatic**: Runs before every deployment
✅ **Tracked**: `alembic_version` table shows current state
✅ **Logged**: CloudWatch logs for debugging
✅ **Secure**: Runs in VPC, uses Secrets Manager

## Common Commands

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history

# Generate SQL without executing
alembic upgrade head --sql
```

## Troubleshooting

**Migration fails in pipeline?**
→ Check CloudWatch logs at `/ecs/dev/migration-task`

**Need to rollback?**
→ Run `alembic downgrade -1` via ECS task

**Migrations out of sync?**
→ Use `alembic stamp head` to mark current state

## Full Documentation

See [docs/DATABASE_MIGRATIONS.md](docs/DATABASE_MIGRATIONS.md) for complete details.
