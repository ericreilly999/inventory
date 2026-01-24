# Browser Cache Issue - 404 Errors

## Problem
You're seeing 404 errors for `/api/v1/locations/` because your browser has cached an old version of the UI JavaScript bundle (`main.8a5e20ea.js`).

## Evidence from Logs
```
GET /api/v1/locations/ HTTP/1.1" 404 Not Found
```

The old UI code is calling `/api/v1/locations/` but the current location service uses `/api/v1/locations/locations` (changed to avoid route conflicts).

## Solution: Hard Refresh Your Browser

### Windows/Linux:
- Press **Ctrl + Shift + R**
- Or **Ctrl + F5**

### Mac:
- Press **Cmd + Shift + R**

### Alternative (Clear Cache):
1. Open Developer Tools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

## Verification
After hard refresh, you should see:
- No more 404 errors for locations
- New JavaScript bundle loaded (different hash than `main.8a5e20ea.js`)
- All location-related pages working correctly

## Current Deployment Status
- Latest commit: `95765ed` (Reports UI fix)
- UI Service: Running task definition revision 20
- All services deployed with latest code
- Location service correctly configured with `/api/v1/locations/locations` endpoint

## Why This Happened
The UI was updated to use the new endpoint structure, but browsers aggressively cache JavaScript bundles. The cached old code is still trying to call the old endpoints.
