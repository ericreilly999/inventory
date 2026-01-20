# UI DataGrid Date Column Fix

## Problem
Multiple pages were throwing errors:
```
Error: MUI: `dateTime` column type only accepts `Date` objects as values.
Use `valueGetter` to transform the value into a `Date` object.
Row ID: 70459f49-b5f8-4b4c-9f8b-83b6a9ad42d3, field: "created_at".
```

## Root Cause
The API returns dates as ISO 8601 strings (e.g., `"2024-01-19T18:07:19.023000-05:00"`), but MUI DataGrid's `dateTime` column type expects JavaScript `Date` objects.

## Solution
Added `valueGetter` to all `dateTime` columns to convert the ISO string to a Date object:

```typescript
{ 
  field: 'created_at', 
  headerName: 'Created', 
  width: 150, 
  type: 'dateTime',
  valueGetter: (params) => params.row.created_at ? new Date(params.row.created_at) : null,
}
```

## Files Fixed

1. **services/ui/src/pages/Users/Users.tsx**
   - Fixed `created_at` column in users DataGrid

2. **services/ui/src/pages/LocationTypes/LocationTypes.tsx**
   - Fixed `created_at` column in location types DataGrid

3. **services/ui/src/pages/Locations/Locations.tsx**
   - Fixed `created_at` column in locations DataGrid

4. **services/ui/src/pages/ItemTypes/ItemTypes.tsx**
   - Fixed `created_at` column in item types DataGrid

5. **services/ui/src/pages/Inventory/Inventory.tsx**
   - Fixed `created_at` column in parent items DataGrid
   - Fixed `created_at` column in child items DataGrid

## Testing
After deployment, these pages should load without errors:
- Users page
- Location Types page
- Locations page
- Item Types page
- Inventory page (both parent and child items tabs)

## Next Steps
Commit and push these changes to trigger the CD pipeline:

```bash
git add services/ui/src/pages/
git commit -m "Fix DataGrid dateTime columns - convert ISO strings to Date objects"
git push origin main
```

The UI service will be rebuilt and deployed automatically.
