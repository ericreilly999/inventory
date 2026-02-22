# Location Reorganization via API - Quick Guide

## Overview
This script reorganizes staging inventory locations by calling the public API endpoints. You can run it from your local machine.

## Prerequisites
- Python 3.7+
- `requests` library: `pip install requests`
- Admin credentials for the staging environment
- Network access to the staging API

## Installation

```bash
# Install required package
pip install requests
```

## Usage

### Step 1: Preview Changes (Recommended First)

```bash
python scripts/reorganize_locations_via_api.py --preview --api-url https://your-staging-url.com
```

You'll be prompted for:
- Username
- Password

The script will show you:
- Which location types will be kept/deleted
- Which locations will be kept/deleted
- How many items will be moved
- Where items will go

### Step 2: Execute Reorganization

After reviewing the preview, execute the changes:

```bash
python scripts/reorganize_locations_via_api.py --execute --api-url https://your-staging-url.com
```

## What It Does

1. **Authenticates** with your credentials
2. **Fetches** all location types and locations
3. **Identifies** what to keep:
   - Location types: Warehouse, Quarantine, Client Site
   - Warehouses/Quarantine: Only those with "JDM" in name
   - Client Sites: All
4. **Moves** all items from deleted locations to JDM warehouse
5. **Deletes** empty locations
6. **Deletes** unused location types

## Examples

### Preview with inline credentials (not recommended for production)
```bash
python scripts/reorganize_locations_via_api.py \
  --preview \
  --api-url https://staging.example.com \
  --username admin \
  --password yourpassword
```

### Execute against staging
```bash
python scripts/reorganize_locations_via_api.py \
  --execute \
  --api-url https://staging.example.com
# Will prompt for credentials
```

### Preview against local dev
```bash
python scripts/reorganize_locations_via_api.py \
  --preview \
  --api-url http://localhost:8000
```

## Expected Output

### Preview Mode
```
Authenticating as admin...
✓ Authentication successful

================================================================================
PREVIEW: Location Reorganization
================================================================================

Fetching location types...

Location Types:
--------------------------------------------------------------------------------
  [KEEP] Warehouse
  [KEEP] Quarantine
  [KEEP] Client Site
  [DELETE] Hospital
  [DELETE] Delivery Site

Fetching locations...

Location Analysis:
--------------------------------------------------------------------------------
  [KEEP] JDM Main Warehouse (Warehouse) - 150 items - JDM location
  [KEEP] JDM Quarantine Zone (Quarantine) - 5 items - JDM location
  [KEEP] Client Site A (Client Site) - 20 items - Client Site (keep all)
  [DELETE] Old Warehouse (Warehouse) - 30 items - No JDM in name
  [DELETE] Hospital A (Hospital) - 10 items - Wrong type: Hospital

Relocation Target:
--------------------------------------------------------------------------------
  Existing JDM Warehouse: JDM Main Warehouse
  Current items: 150
  After relocation: 190

================================================================================
Summary:
================================================================================
Location types to keep: 3
Location types to delete: 2
Locations to keep: 3
Locations to delete: 2
Items to relocate: 40

================================================================================
This is a PREVIEW only - no changes have been made
Run with --execute to apply changes
================================================================================
```

### Execute Mode
```
Authenticating as admin...
✓ Authentication successful

================================================================================
EXECUTING: Location Reorganization
================================================================================

Step 1: Fetching location types...

Step 2: Fetching locations...
  Locations to keep: 3
  Locations to delete: 2

Step 3: Preparing relocation target...
  Using existing JDM warehouse: JDM Main Warehouse

Step 4: Relocating items...

  Processing: Old Warehouse (30 items)
    ✓ Moved item SKU-001
    ✓ Moved item SKU-002
    ...

  Total items moved: 40

Step 5: Deleting empty locations...
  Deleting: Old Warehouse
    ✓ Deleted
  Deleting: Hospital A
    ✓ Deleted

  Locations deleted: 2

Step 6: Deleting unused location types...
  Deleting location type: Hospital
    ✓ Deleted
  Deleting location type: Delivery Site
    ✓ Deleted

  Location types deleted: 2

================================================================================
✓ Location reorganization completed!
================================================================================
Items relocated: 40
Locations deleted: 2
Location types deleted: 2
```

## Troubleshooting

### Authentication Failed
- Verify your username and password
- Check that your user has admin permissions
- Verify the API URL is correct

### Connection Error
- Check that the API is accessible from your machine
- Verify the URL (include https:// or http://)
- Check firewall/VPN settings

### Permission Denied
- Your user needs admin role for location management
- Contact your administrator to grant permissions

### Items Failed to Move
- Check that the target JDM warehouse exists
- Verify items are not locked or in use
- Check API logs for specific errors

## Safety Features

- **Preview mode**: See changes before applying
- **Authentication required**: Must have valid admin credentials
- **API validation**: All operations validated by backend
- **Transaction safety**: API handles rollback on errors
- **Detailed logging**: See exactly what's happening

## Verification

After running, verify the results:

1. **Check the UI**: Browse locations and inventory
2. **Check via API**:
   ```bash
   # List location types
   curl -H "Authorization: Bearer $TOKEN" https://staging.example.com/api/location-types
   
   # List locations with item counts
   curl -H "Authorization: Bearer $TOKEN" https://staging.example.com/api/locations/with-items
   ```

## Rollback

If something goes wrong:
1. Restore from database backup
2. Contact your administrator

## Notes

- The script uses the public API, so it respects all business rules and validations
- All operations are logged on the server side
- Move history is preserved for audit trail
- The script can be run multiple times safely (idempotent for most operations)

## Support

For issues:
1. Check the script output for error messages
2. Check API server logs
3. Verify your permissions
4. Contact the development team
