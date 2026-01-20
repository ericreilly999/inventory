# GitHub Secrets Quick Start

## What You Need

Two secrets must be configured in GitHub before the workflow can run:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret key

## Quick Setup (5 minutes)

### Option 1: Use Existing AWS Credentials

If you already have AWS CLI configured:

```bash
# Get your current credentials
aws configure get aws_access_key_id
aws configure get aws_secret_access_key
```

Then add these to GitHub:
1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `AWS_ACCESS_KEY_ID` with the access key value
4. Add `AWS_SECRET_ACCESS_KEY` with the secret key value

### Option 2: Create New IAM User (Recommended)

```bash
# 1. Create user
aws iam create-user --user-name github-actions-deploy

# 2. Attach policies (use AWS managed policies for quick setup)
aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

# 3. Create access key
aws iam create-access-key --user-name github-actions-deploy
```

Copy the AccessKeyId and SecretAccessKey from the output and add them to GitHub secrets.

## Add Secrets to GitHub

1. **Navigate**: Your Repo → Settings → Secrets and variables → Actions
2. **Click**: "New repository secret"
3. **Add**:
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: Your access key ID
4. **Click**: "Add secret"
5. **Repeat** for `AWS_SECRET_ACCESS_KEY`

## Verify Setup

After adding secrets, you should see:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY

## Test It

```bash
# Create a test branch
git checkout -b test-github-actions

# Make an empty commit
git commit --allow-empty -m "Test GitHub Actions"

# Push it
git push origin test-github-actions
```

Then check GitHub → Actions tab to see if the workflow runs.

## Troubleshooting

**Error: "Credentials could not be loaded"**
- Check secret names are exactly `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (case-sensitive)

**Error: "AccessDenied"**
- IAM user needs ECR and ECS permissions
- See `docs/GITHUB-SECRETS-SETUP.md` for detailed policy

**Error: "User not authorized"**
- Check IAM policy is attached to the user
- Verify user has access to your specific ECS cluster

## Need More Help?

See `docs/GITHUB-SECRETS-SETUP.md` for:
- Detailed IAM policy configuration
- Security best practices
- Step-by-step screenshots
- Advanced troubleshooting

## Ready to Deploy?

Once secrets are configured, follow `READY-TO-DEPLOY.md` to deploy your fixes.
