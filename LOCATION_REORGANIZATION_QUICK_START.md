# Location Reorganization - Quick Start Guide

## Overview
This guide shows you how to reorganize staging inventory locations using GitHub Actions.

## What It Does
- Keeps only: Warehouse (with "JDM"), Quarantine (with "JDM"), and all Client Sites
- Moves all inventory from deleted locations to JDM warehouse
- Deletes empty locations and unused location types

## Prerequisites
- GitHub repository access
- AWS credentials configured in GitHub Secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ACCOUNT_ID`

## Step-by-Step Instructions

### Step 1: Check Current Status (Optional)
1. Go to GitHub repository
2. Click **Actions** tab
3. Select **Run Location Reorganization (ECS)** workflow
4. Click **Run workflow** button
5. Select `action: check`
6. Click **Run workflow**
7. Wait for completion (~2-3 minutes)
8. Review output to see current locations and item counts

### Step 2: Preview Changes (Recommended)
1. Go to **Actions** tab
2. Select **Run Location Reorganization (ECS)** workflow
3. Click **Run workflow** button
4. Select `action: preview`
5. Click **Run workflow**
6. Wait for completion (~2-3 minutes)
7. Review output carefully:
   - Which locations will be kept
   - Which locations will be deleted
   - How many items will be moved
   - Where items will go

### Step 3: Execute Reorganization
⚠️ **IMPORTANT**: Only proceed if preview looks correct!

1. Go to **Actions** tab
2. Select **Run Location Reorganization (ECS)** workflow
3. Click **Run workflow** button
4. Select `action: execute`
5. Click **Run workflow**
6. Wait for completion (~3-5 minutes)
7. Review output for success confirmation

### Step 4: Verify Results
Connect to your staging database and run:

```sql
-- Check remaining location types
SELECT lt.name, COUNT(l.id) as location_count
FROM location_types lt
LEFT JOIN locations l ON l.location_type_id = lt.id
GROUP BY lt.name;

-- Check all locations
SELECT l.name, lt.name as type, COUNT(pi.id) as items
FROM locations l
JOIN location_types lt ON l.location_type_id = lt.id
LEFT JOIN parent_items pi ON pi.current_location_id = l.id
GROUP BY l.id, l.name, lt.name
ORDER BY lt.name, l.name;
```

## Expected Results

### Before
- Multiple location types (Hospital, Delivery Site, etc.)
- Multiple warehouses and quarantine locations
- Items spread across many locations

### After
- Only 3 location types: Warehouse, Quarantine, Client Site
- Only JDM warehouses and quarantine locations
- All items consolidated into JDM locations or client sites

## Troubleshooting

### Workflow Fails
1. Check workflow logs in GitHub Actions
2. Check CloudWatch Logs: `/ecs/staging/location-reorganization`
3. Verify AWS credentials are valid
4. Verify database secret exists: `staging/inventory-management/database`

### Need to Rollback
If something goes wrong:
1. Restore from database backup
2. Contact development team

## Safety Features
- ✓ Preview mode shows changes before applying
- ✓ All changes in single transaction (auto-rollback on error)
- ✓ Verifies all items moved before deleting locations
- ✓ Detailed logging in CloudWatch
- ✓ Runs securely within VPC

## Support
- Detailed docs: `docs/LOCATION_REORGANIZATION.md`
- Full summary: `TASK_COMPLETION_SUMMARY.md`
- Contact: Development team

## Quick Reference

| Action | Purpose | Safe? | Duration |
|--------|---------|-------|----------|
| check | View current status | ✓ Yes | ~2 min |
| preview | See what will happen | ✓ Yes | ~2 min |
| execute | Apply changes | ⚠️ No | ~3-5 min |

**Always run preview before execute!**
