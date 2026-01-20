# UI Dockerfile Fix

## Problem
The UI service build was failing with:
```
Could not find a required file.
  Name: index.html
  Searched in: /app/public
```

## Root Cause
The Dockerfile was using `COPY services/ui/ .` which should copy all files, but the build process couldn't find the `public/index.html` file. This could be due to:
1. The way Docker handles the COPY command with trailing slashes
2. Potential timing issues with how files are copied
3. The previous `--omit=dev` flag (though react-scripts is in dependencies, not devDependencies)

## Solution
Made the Dockerfile more explicit by:
1. Copying `package*.json` files first (for better Docker layer caching)
2. Running `npm install` (without `--omit=dev` to ensure all dependencies are available)
3. Explicitly copying required directories:
   - `services/ui/public` → `/app/public`
   - `services/ui/src` → `/app/src`
   - `services/ui/tsconfig.json` → `/app/tsconfig.json`

This ensures the directory structure is exactly as expected by react-scripts.

## Changes Made
File: `services/ui/Dockerfile`

**Before:**
```dockerfile
COPY services/ui/package.json services/ui/package-lock.json* ./
RUN npm install --omit=dev
COPY services/ui/ .
```

**After:**
```dockerfile
COPY services/ui/package*.json ./
RUN npm install
COPY services/ui/public ./public
COPY services/ui/src ./src
COPY services/ui/tsconfig.json ./
```

## Benefits
1. **Explicit structure**: No ambiguity about where files go
2. **Better caching**: Package files copied separately for Docker layer caching
3. **All dependencies**: No `--omit=dev` flag that might skip needed packages
4. **Clearer intent**: Easy to see exactly what's being copied

## Testing
After committing and pushing to main, the GitHub Actions CD workflow will:
1. Build the UI service with the fixed Dockerfile
2. Tag it with the commit SHA
3. Push to ECR
4. Create a new task definition
5. Deploy to ECS

## Verification
After deployment:
```bash
aws ecs describe-services --cluster dev-inventory-cluster --services dev-ui-service --region us-west-2 --query "services[0].taskDefinition"
```

Should show a new task definition revision (5 or higher).
