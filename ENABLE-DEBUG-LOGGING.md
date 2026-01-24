# Enable Debug Logging for Location Service

## Changes Made

Added comprehensive debug logging to the location service to diagnose the 422 errors.

### 1. Enable FastAPI Debug Mode
```python
app = FastAPI(
    ...
    debug=True  # Enable debug mode
)
```

### 2. Custom Validation Error Handler
Added a custom exception handler that logs detailed validation errors:
- Request path and method
- Validation error details
- Request body
- Returns detailed error response to help diagnose issues

### 3. Request/Response Logging Middleware
Added middleware to log:
- All incoming requests with method, path, query params, and headers
- All responses with status codes
- Excludes sensitive headers (authorization, cookie)

## What This Will Show

After deployment, the CloudWatch logs will show:
1. **Incoming requests**: Exact path, method, and parameters
2. **Validation errors**: Detailed error messages showing what field failed validation and why
3. **Response status**: Whether the request succeeded or failed

## How to View Logs

```bash
# Tail the logs in real-time
aws logs tail /ecs/dev-inventory --region us-west-2 --since 5m --follow --filter-pattern "Location Service"

# Or search for validation errors
aws logs tail /ecs/dev-inventory --region us-west-2 --since 10m --filter-pattern "Validation error"
```

## Expected Output

When the 422 error occurs, you'll see something like:
```json
{
  "event": "Validation error",
  "path": "/api/v1/locations/types",
  "method": "GET",
  "errors": [
    {
      "loc": ["query", "some_param"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

This will tell us exactly what's causing the validation failure.

## Deployment

```bash
git add services/location/main.py ENABLE-DEBUG-LOGGING.md
git commit -m "Enable debug logging for location service to diagnose 422 errors"
git push origin main
```

## After Deployment

1. Wait for deployment to complete (2-3 minutes)
2. Try accessing the location types page
3. Check CloudWatch logs for detailed error messages
4. The logs will show exactly what's wrong
