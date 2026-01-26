# Login Issue Debug Findings

## Current Status
Login with admin/admin is failing with "Incorrect username or password" (401 Unauthorized)

## Key Findings from Debug

### Seed Database Endpoint Test (Working)
```json
{
  "message": "Admin user already exists - password hash updated",
  "username": "admin",
  "status": "updated",
  "debug_info": {
    "user_id": "64a922aa-ba92-43c8-898d-ed8e8418ef71",
    "active": true,
    "old_hash_prefix": "$2b$12$8xBVsBuUePCg3",
    "new_hash_prefix": "$2b$12$djVJae1aZwvvl",
    "password_verification_test": true
  }
}
```

**Analysis:**
- ✅ Admin user exists in database
- ✅ User is active (active: true)
- ✅ Password hash was updated successfully
- ✅ Password verification test PASSED (password_verification_test: true)
- ✅ The bcrypt hash/verify cycle works correctly

### Login Endpoint Test (Failing)
```
POST /api/v1/auth/login
Body: {"username":"admin","password":"admin"}
Response: 401 {"detail":"Incorrect username or password"}
```

**Analysis:**
- ❌ Login fails despite correct credentials
- ❌ CloudWatch logs show "User not found for login attempt"

## Root Cause Analysis

The seed endpoint successfully:
1. Finds the admin user
2. Updates the password hash
3. Verifies the password hash works

But the login endpoint fails with "User not found". This suggests:

### Hypothesis 1: Database Session/Connection Issue
The seed endpoint and login endpoint might be using different database sessions or connections, causing the login endpoint to not see the updated user.

### Hypothesis 2: Query Difference
The login endpoint query is:
```python
user = (
    db.query(User)
    .options(joinedload(User.role))
    .filter(User.username == user_credentials.username, User.active is True)
    .first()
)
```

The seed endpoint query is:
```python
existing_admin = db.query(User).filter(User.username == "admin").first()
```

The difference is:
- Login uses `joinedload(User.role)` - might cause issues
- Login filters by `active is True` - but we confirmed user is active
- Login uses `user_credentials.username` - might have whitespace or encoding issues

### Hypothesis 3: API Gateway Routing
The requests might be going through the API gateway which could be:
- Routing to different service instances
- Modifying the request body
- Adding authentication that interferes

## Next Steps

1. ✅ Confirmed user exists and is active
2. ✅ Confirmed password hash is correct and verifies
3. ⏳ Need to investigate why login endpoint can't find the user
4. ⏳ Check if API gateway is routing correctly
5. ⏳ Add more debug logging to login endpoint
6. ⏳ Test direct connection to user-service (bypass API gateway)

## Code Changes Made

1. Replaced passlib with direct bcrypt usage
2. Updated password hashing to use bcrypt.gensalt() and bcrypt.hashpw()
3. Updated password verification to use bcrypt.checkpw()
4. Added debug logging to login endpoint
5. Updated seed endpoint to refresh password hash when user exists
6. Added debug info to seed endpoint response

## Test Results

- ✅ 382 tests passing in CI/CD
- ✅ Bcrypt hash/verify works correctly in isolation
- ✅ Seed endpoint works and updates password
- ✅ Password verification test passes
- ❌ Login endpoint still fails to find user
