# Location Reorganization via API - Summary

## What I Created

I've created a Python script that reorganizes locations using your public API endpoints instead of direct database access. This solves the connectivity issue since you can run it from your local machine.

## Files Created

1. **`scripts/reorganize_locations_via_api.py`** - Main script
2. **`REORGANIZE_VIA_API_GUIDE.md`** - Detailed usage guide
3. **`API_REORGANIZATION_SUMMARY.md`** - This file

## How It Works

The script uses these API endpoints:
- `POST /api/auth/login` - Authenticate
- `GET /api/location-types` - List location types
- `GET /api/locations/with-items` - List locations with item counts
- `GET /api/locations/{id}/items` - Get items at a location
- `POST /api/movements/move` - Move items between locations
- `DELETE /api/locations/{id}` - Delete a location
- `DELETE /api/location-types/{id}` - Delete a location type

## Quick Start

### 1. Install Dependencies
```bash
pip install requests
```

### 2. Preview Changes
```bash
python scripts/reorganize_locations_via_api.py --preview --api-url https://YOUR-STAGING-URL
```

### 3. Execute (after reviewing preview)
```bash
python scripts/reorganize_locations_via_api.py --execute --api-url https://YOUR-STAGING-URL
```

## What You Need

1. **Staging API URL** - The public URL for your staging environment
2. **Admin Credentials** - Username and password with admin permissions
3. **Python 3.7+** with `requests` library

## Business Rules (Same as Before)

- Keep: Warehouse (with "JDM"), Quarantine (with "JDM"), Client Site (all)
- Delete: All other location types
- Move: All inventory to JDM warehouse before deletion

## Advantages of API Approach

✅ **No VPC/Database Access Needed** - Works from anywhere
✅ **Uses Existing Business Logic** - All API validations apply
✅ **Audit Trail** - Move history preserved
✅ **Safe** - Preview mode shows changes first
✅ **Simple** - Just run a Python script locally

## Next Steps

1. **Find your staging API URL**
   - Check your ALB/Load Balancer DNS name
   - Or check your Route53 records
   - Should be something like: `https://staging-api.yourdomain.com`

2. **Test with preview**
   ```bash
   python scripts/reorganize_locations_via_api.py \
     --preview \
     --api-url https://YOUR-STAGING-URL
   ```

3. **Review the output carefully**

4. **Execute if everything looks good**
   ```bash
   python scripts/reorganize_locations_via_api.py \
     --execute \
     --api-url https://YOUR-STAGING-URL
   ```

## Example Session

```bash
$ python scripts/reorganize_locations_via_api.py --preview --api-url https://staging.example.com
Username: admin
Password: ********

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

... (detailed output) ...

================================================================================
Summary:
================================================================================
Location types to keep: 3
Location types to delete: 2
Locations to keep: 13
Locations to delete: 5
Items to relocate: 40

================================================================================
This is a PREVIEW only - no changes have been made
Run with --execute to apply changes
================================================================================
```

## Troubleshooting

### Can't find staging URL?
Check your terraform outputs or AWS console:
```bash
cd terraform/environments/staging
terraform output alb_dns_name
```

### Authentication fails?
- Verify credentials work in the UI first
- Make sure user has admin role
- Check API is accessible

### Script errors?
- Make sure `requests` is installed: `pip install requests`
- Check Python version: `python --version` (need 3.7+)
- Verify API URL is correct (include https://)

## What's Different from Database Approach?

| Aspect | Database Script | API Script |
|--------|----------------|------------|
| Connectivity | Needs VPC access | Works from anywhere |
| Authentication | Database credentials | User credentials |
| Validation | Manual | Automatic (via API) |
| Audit Trail | Manual | Automatic |
| Rollback | Transaction | API handles it |
| Complexity | High | Low |

## Safety

- Preview mode shows all changes before applying
- All operations go through API validation
- Move history is automatically created
- Can be run multiple times safely
- No direct database access needed

## Ready to Run!

The script is ready to use. Just need:
1. Your staging API URL
2. Admin credentials
3. Run the preview first

Let me know your staging URL and we can test it!
