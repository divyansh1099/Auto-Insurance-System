#!/bin/bash

set -e

# Script to build and push Docker images to ECR

echo "========================================="
echo "Building and Pushing Docker Images"
echo "========================================="

# Check if we're in the terraform directory
if [ ! -f "main.tf" ]; then
    echo "❌ Please run this script from the terraform directory"
    exit 1
fi

# Get AWS region and account
REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get ECR repository URLs
BACKEND_REPO=$(terraform output -raw ecr_backend_repository_url 2>/dev/null || echo "")
SIMULATOR_REPO=$(terraform output -raw ecr_simulator_repository_url 2>/dev/null || echo "")

if [ -z "$BACKEND_REPO" ] || [ -z "$SIMULATOR_REPO" ]; then
    echo "❌ ECR repositories not found. Please run 'terraform apply' first."
    exit 1
fi

echo "Region: $REGION"
echo "Backend Repository: $BACKEND_REPO"
echo "Simulator Repository: $SIMULATOR_REPO"
echo ""

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Build and push backend
echo ""
echo "Building backend image..."
cd ..
docker build -t telematics-insurance/backend:latest ./backend

echo "Tagging backend image..."
docker tag telematics-insurance/backend:latest ${BACKEND_REPO}:latest

echo "Pushing backend image..."
docker push ${BACKEND_REPO}:latest

# Build and push simulator
echo ""
echo "Building simulator image..."
docker build -t telematics-insurance/simulator:latest ./simulator

echo "Tagging simulator image..."
docker tag telematics-insurance/simulator:latest ${SIMULATOR_REPO}:latest

echo "Pushing simulator image..."
docker push ${SIMULATOR_REPO}:latest

echo ""
echo "========================================="
echo "✅ Images pushed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update ECS service to use new image:"
echo "   aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment"
echo ""
echo "2. Or the service will automatically pull the latest image on next deployment"

