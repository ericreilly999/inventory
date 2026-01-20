# GitHub Secrets Setup Guide

## Required Secrets

Your GitHub Actions workflow requires the following secrets to be configured:

### 1. AWS_ACCESS_KEY_ID
**Purpose**: AWS access key for authenticating with AWS services (ECR, ECS)

**How to get it**:
1. Go to AWS Console → IAM → Users
2. Select your deployment user (or create one)
3. Go to "Security credentials" tab
4. Click "Create access key"
5. Choose "Application running outside AWS"
6. Copy the Access Key ID

**Required Permissions**:
The IAM user needs these permissions:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`
- `ecr:DescribeImages`
- `ecs:UpdateService`
- `ecs:DescribeServices`
- `ecs:ListTasks`
- `ecs:DescribeTasks`

### 2. AWS_SECRET_ACCESS_KEY
**Purpose**: AWS secret key (paired with the access key above)

**How to get it**:
- This is shown only once when you create the access key
- Copy it immediately and store it securely
- If you lose it, you'll need to create a new access key

### 3. GITHUB_TOKEN (Optional)
**Purpose**: Used by dependency update workflows

**Note**: This is automatically provided by GitHub Actions. You don't need to set it manually.

## How to Add Secrets to GitHub

### Step 1: Navigate to Repository Settings
1. Go to your GitHub repository
2. Click "Settings" tab
3. In the left sidebar, click "Secrets and variables" → "Actions"

### Step 2: Add Each Secret
1. Click "New repository secret"
2. Enter the secret name (e.g., `AWS_ACCESS_KEY_ID`)
3. Paste the secret value
4. Click "Add secret"
5. Repeat for each secret

### Step 3: Verify Secrets Are Added
You should see these secrets listed:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY

## Creating an IAM User for GitHub Actions

If you don't have an IAM user yet, here's how to create one:

### Step 1: Create IAM User
```bash
aws iam create-user --user-name github-actions-deploy
```

### Step 2: Create IAM Policy
Save this as `github-actions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeImages",
        "ecr:DescribeRepositories"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "ecs:StopTask"
      ],
      "Resource": [
        "arn:aws:ecs:us-west-2:290993374431:service/dev-inventory-cluster/*",
        "arn:aws:ecs:us-west-2:290993374431:task/dev-inventory-cluster/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:ListServices",
        "ecs:ListClusters"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Attach Policy to User
```bash
# Create the policy
aws iam create-policy \
  --policy-name GitHubActionsDeployPolicy \
  --policy-document file://github-actions-policy.json

# Attach to user
aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::290993374431:policy/GitHubActionsDeployPolicy
```

### Step 4: Create Access Key
```bash
aws iam create-access-key --user-name github-actions-deploy
```

This will output:
```json
{
  "AccessKey": {
    "AccessKeyId": "AKIA...",
    "SecretAccessKey": "wJalrXUtn...",
    "Status": "Active",
    "CreateDate": "2024-01-19T..."
  }
}
```

Copy both values and add them to GitHub secrets.

## Alternative: Use Existing AWS Credentials

If you already have AWS credentials configured locally:

### Option 1: Use Your Current Credentials
```bash
# View your current access key ID
aws configure get aws_access_key_id

# View your current secret key (be careful with this!)
aws configure get aws_secret_access_key
```

**Warning**: Only use personal credentials if:
- You have the necessary permissions
- You're comfortable with GitHub Actions using your credentials
- This is for development/testing only

### Option 2: Use AWS CLI to Get Credentials
If you're using AWS SSO or temporary credentials, you'll need to create a dedicated IAM user as shown above.

## Testing the Setup

After adding secrets, test the workflow:

1. **Trigger a test workflow**:
   ```bash
   git checkout -b test-github-actions
   git commit --allow-empty -m "Test GitHub Actions setup"
   git push origin test-github-actions
   ```

2. **Check the workflow**:
   - Go to GitHub → Actions tab
   - You should see the workflow running
   - If it fails on "Configure AWS credentials", check your secrets

3. **Common Issues**:
   - ❌ "Error: Credentials could not be loaded" → Check secret names match exactly
   - ❌ "AccessDenied" → IAM user needs more permissions
   - ❌ "User not authorized" → Check IAM policy is attached

## Security Best Practices

1. **Use Least Privilege**: Only grant permissions needed for deployment
2. **Rotate Keys Regularly**: Create new access keys every 90 days
3. **Monitor Usage**: Check CloudTrail for unexpected API calls
4. **Use Separate User**: Don't use your personal AWS credentials
5. **Enable MFA**: Consider requiring MFA for sensitive operations

## Verification Checklist

Before running the workflow, verify:

- ✅ IAM user created with deployment permissions
- ✅ Access key created and saved securely
- ✅ `AWS_ACCESS_KEY_ID` added to GitHub secrets
- ✅ `AWS_SECRET_ACCESS_KEY` added to GitHub secrets
- ✅ Secret names match exactly (case-sensitive)
- ✅ IAM user has ECR and ECS permissions
- ✅ IAM user can access your specific cluster and repositories

## Next Steps

Once secrets are configured:

1. Commit your code changes
2. Push to GitHub
3. Create a pull request
4. Merge to main
5. Watch the GitHub Actions workflow deploy your services

See `READY-TO-DEPLOY.md` for deployment instructions.
