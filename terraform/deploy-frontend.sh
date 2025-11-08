#!/bin/bash

set -e

# Script to build and deploy frontend to S3/CloudFront

echo "========================================="
echo "Deploying Frontend to S3/CloudFront"
echo "========================================="

# Check if we're in the terraform directory
if [ ! -f "main.tf" ]; then
    echo "❌ Please run this script from the terraform directory"
    exit 1
fi

# Get AWS region
REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME=$(terraform output -raw project_name 2>/dev/null || echo "telematics-insurance")

BUCKET_NAME="${PROJECT_NAME}-frontend-${ACCOUNT_ID}"

echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
echo ""

# Build frontend
echo "Building frontend..."
cd ../frontend

if [ ! -f "package.json" ]; then
    echo "❌ Frontend directory not found. Please run from terraform directory."
    exit 1
fi

npm install
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed. dist/ directory not found."
    exit 1
fi

# Upload to S3
echo ""
echo "Uploading to S3..."
aws s3 sync dist/ s3://${BUCKET_NAME}/ --delete --region $REGION

# Set proper content types
aws s3 cp s3://${BUCKET_NAME}/ s3://${BUCKET_NAME}/ --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --metadata-directive REPLACE
aws s3 cp s3://${BUCKET_NAME}/ s3://${BUCKET_NAME}/ --recursive --exclude "*" --include "*.css" --content-type "text/css" --metadata-directive REPLACE

# Invalidate CloudFront cache
echo ""
echo "Invalidating CloudFront cache..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Comment, '${PROJECT_NAME}-frontend')].Id" \
    --output text \
    --region $REGION)

if [ ! -z "$DISTRIBUTION_ID" ]; then
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text \
        --region $REGION)
    echo "✅ CloudFront invalidation created: $INVALIDATION_ID"
else
    echo "⚠️  CloudFront distribution not found. Skipping cache invalidation."
fi

# Get CloudFront URL
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url 2>/dev/null || echo "")
if [ ! -z "$CLOUDFRONT_URL" ]; then
    echo ""
    echo "========================================="
    echo "✅ Frontend deployed successfully!"
    echo "========================================="
    echo ""
    echo "Frontend URL: https://${CLOUDFRONT_URL}"
    echo "S3 Website URL: http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com"
else
    echo ""
    echo "✅ Frontend uploaded to S3"
    echo "   Run 'terraform output cloudfront_url' to get the CDN URL"
fi

