# Root Cause Analysis: Why Deployments Weren't Working

## The Problem

You correctly identified that the services were still on task definition version 4 even after multiple deployment attempts. The new code wasn't running.

## Root Cause

### Issue 1: Using `:latest` Tag with ECS Caching
- Task definitions pointed to images with `:latest` tag
- ECS caches Docker images aggressively
- `force-new-deployment` only restarts tasks with the SAME task definition
- It doesn't pull new images if the tag hasn't changed
- Result: Old code kept running even after pushing new images

### Issue 2: Not Creating New Task Definitions
- The CD workflow was calling `aws ecs update-service --force-new-deployment`
- This doesn't update the task definition itself
- It just restarts tasks using the existing task definition
- The task definition still pointed to `:latest` which was cached
- Result: Same old image kept being used

## The Solution

### Use Commit SHA Tags Instead of `:latest`

**Why this works:**
1. Each commit gets a unique image tag (e.g., `abc123f`)
2. New task definition is created with the new image tag
3. ECS sees it's a different image and pulls it
4. No caching issues because the tag is unique

**Implementation:**
1. Build image: `docker build -t service:$SHA`
2. Push with SHA tag: `docker push registry/service:$SHA`
3. Update task definition to use `registry/service:$SHA`
4. Register new task definition (creates new revision)
5. Update service to use new task definition revision

### What We Fixed

#### 1. CD Workflow (`.github/workflows/cd.yml`)
**Before:**
```yaml
tags: |
  type=raw,value=latest
```
- Only tagged with `latest`
- Didn't create new task definitions
- Just called `force-new-deployment`

**After:**
```yaml
tags: |
  type=sha,prefix=,format=short  # e.g., abc123f
  type=raw,value=latest
```
- Tags with commit SHA AND latest
- Creates new task definition with SHA-tagged image
- Updates service to use new task definition revision

#### 2. Deployment Process
**Before:**
```bash
aws ecs update-service --force-new-deployment
```
- Restarts tasks with same task definition
- Same `:latest` image (cached)

**After:**
```bash
# 1. Get current task definition
# 2. Update image to use SHA tag
# 3. Register NEW task definition
# 4. Update service to use NEW task definition
aws ecs update-service --task-definition service:NEW_REVISION
```
- Creates new task definition with new image
- Service uses new task definition
- New image is pulled

## Why Your Suggestion Was Correct

You suggested:
> "maybe we should switched to tag-based docker images instead of using latest"

This was exactly right because:
1. `:latest` is mutable - same tag, different content
2. ECS caches by tag, not by content
3. Unique tags (like commit SHA) force ECS to pull new images
4. New task definitions with new tags = guaranteed deployment

## Verification

After deploying with SHA tags, you should see:
```bash
aws ecs describe-services --cluster dev-inventory-cluster --services dev-location-service
```

Output should show:
- Task definition revision increased (e.g., from `:4` to `:5`)
- Image tag includes commit SHA (not just `:latest`)
- Running count matches desired count

## Manual Deployment Commands

See `DEPLOY-NOW.md` for step-by-step commands to deploy right now with SHA tags.

## Future Deployments

Once you merge the updated CD workflow to main:
1. Push code to main branch
2. GitHub Actions automatically:
   - Builds images with commit SHA tags
   - Pushes to ECR
   - Creates new task definitions
   - Updates services
3. New code runs immediately

## Key Takeaways

1. **Never use `:latest` in production** - Always use immutable tags
2. **Commit SHA is ideal** - Unique, traceable, immutable
3. **New task definition = new deployment** - Don't just restart tasks
4. **ECS caches aggressively** - Unique tags bypass the cache

## Additional Benefits of SHA Tags

1. **Traceability**: Know exactly which commit is running
2. **Rollback**: Easy to rollback to specific commit
3. **Debugging**: Match logs to exact code version
4. **No cache issues**: Each deployment is guaranteed fresh
5. **Audit trail**: Clear deployment history

## Next Steps

1. Run the manual deployment commands in `DEPLOY-NOW.md`
2. Verify services update to new task definition revisions
3. Test the application (log out/in first for new JWT)
4. Commit and merge the CD workflow fixes
5. Future deployments will be automatic and reliable
