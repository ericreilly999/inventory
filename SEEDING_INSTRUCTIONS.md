# Data Seeding Instructions

## Overview

The inventory system now has comprehensive data seeding scripts that create test data with proper SKU formatting and respect API rate limits.

## Rate Limiting

**Important**: The API Gateway has rate limiting enabled:
- **Limit**: 100 requests per 60 seconds (1 minute)
- **Location**: `services/api_gateway/middleware/rate_limit_middleware.py`
- **Configuration**: `shared/config/settings.py` (RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

The seeding script uses **1 second delays** between requests to stay well under this limit.

## SKU Format

Parent item SKUs are now **simple numeric values** (1, 2, 3, etc.) as requested:
- ✅ Correct: `1`, `2`, `3`
- ❌ Incorrect: `Sports Tower 1`, `MedEd 1688 2`

The item type is stored in a separate field, so including it in the SKU is redundant.

Child item SKUs follow the format: `{parent_sku}-{child_type_name}`
- Example: `1-Crossfire`, `2-1688 CCU`, `3-OLED Monitor`

## Scripts

### 1. Rollback Script (`scripts/rollback_seed_data.py`)

Removes all seeded test data:
```bash
python scripts/rollback_seed_data.py
```

This will:
- Delete all parent items (cascades to child items)
- Delete custom item types (keeps default types: Equipment, Furniture, Component, Accessory)

### 2. Seeding Script (`scripts/seed_inventory_data.py`)

Creates comprehensive test data:
```bash
python scripts/seed_inventory_data.py
```

**Estimated Runtime**: 8-10 minutes (due to rate limiting and 1-second delays)

## What Gets Created

### Item Types
- **7 Parent Types**: RISE Tower, 1788 Roll Stand, 1688 Roll Stand, MedEd 1688, Clinical 1788, MedEd 1788, Sports Tower
- **19 Child Types**: Various CCUs, Light Sources, Monitors, Accessories

### Parent Items (70 total)
Each type gets 10 items (SKUs 1-10):
- 9 distributed across warehouse locations
- 1 at Test Client Site
- 1 in a quarantine location (SKU 11)

### Child Items (~280 total)
Each parent item gets its appropriate child items:

- **Sports Tower**: Crossfire, Crossflow, Light Source (random), Vision Pro Monitor
- **MedEd 1688**: 1688 CCU, L11 Light Source, Pneumoclear, OLED Monitor, OR Hub (optional)
- **MedEd 1788**: 1788 CCU, L12 Light Source, Pneumoclear, OR Hub (optional)
- **Clinical 1788**: OR Hub, 1788 CCU, L12 Light Source, Printer, Pinpoint, OLED Monitor
- **RISE Tower**: OR Hub, 1688 CCU, L11 Light Source, Printer, Pinpoint
- **1788 Roll Stand**: Pole, Base, OLED Monitor
- **1688 Roll Stand**: Pole, Base

### Movements (100 total)
Random movements between locations to create movement history for reporting.

## Locations Used

The script distributes items across:
- **5 Warehouse locations**: JDM Austin, JDM Chicago, JDM Las Vegas, JDM NY, JDM Tampa
- **2 Client Site locations**: Including Test Client Site
- **5 Quarantine locations**: Various quarantine areas

## Troubleshooting

### Rate Limit Errors
If you see "Internal Server Error" or rate limit messages:
- The script already has 1-second delays
- The API limit is 100 requests/minute
- Consider running the script during off-peak hours

### Duplicate SKU Errors
If you see duplicate SKU errors:
- Run the rollback script first: `python scripts/rollback_seed_data.py`
- Then run the seeding script again

### Connection Timeouts
If the script times out:
- Check that the API is accessible: `curl http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com/health`
- Verify your network connection
- The database might be under heavy load

## Verification

After seeding, verify the data:

1. **Check item counts**:
   - Navigate to Inventory Management in the UI
   - You should see 70 parent items across all types
   - Each parent should have its child items

2. **Check movements**:
   - Navigate to Reports
   - Generate a Movement History Report
   - You should see 100 movements

3. **Check dashboard**:
   - Navigate to Dashboard
   - Select a location type
   - You should see inventory and throughput data

## Performance Notes

- **Total Requests**: ~476 (26 item types + 70 parents + 280 children + 100 movements)
- **With 1s delays**: ~8 minutes total runtime
- **Rate limit**: 100 req/min = stays under limit at 60 req/min
- **Database**: Uses API endpoints, not direct DB access

## Next Steps

After seeding:
1. Test inventory management features
2. Test movement tracking
3. Generate reports with real data
4. Test filtering and search
5. Verify dashboard displays correctly

## Files

- `scripts/seed_inventory_data.py` - Main seeding script
- `scripts/rollback_seed_data.py` - Cleanup script
- `services/api_gateway/middleware/rate_limit_middleware.py` - Rate limiting logic
- `shared/config/settings.py` - Rate limit configuration
