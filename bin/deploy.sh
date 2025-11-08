#!/bin/bash

set -e

echo "========================================="
echo "AWS Deployment Script"
echo "Telematics Insurance System"
echo "========================================="

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform first."
    echo "   Visit: https://www.terraform.io/downloads"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install AWS CLI first."
    echo "   Visit: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✅ Terraform and AWS CLI are installed"

# Check AWS credentials
echo ""
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    echo "   Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS credentials configured (Account: $ACCOUNT_ID)"

# Check for terraform.tfvars
if [ ! -f terraform.tfvars ]; then
    echo ""
    echo "⚠️  terraform.tfvars not found. Creating from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo "✅ Created terraform.tfvars"
    echo "   Please review and update terraform.tfvars before proceeding"
    read -p "Press Enter to continue after updating terraform.tfvars..."
fi

# Initialize Terraform
echo ""
echo "Initializing Terraform..."
terraform init

# Plan
echo ""
echo "Running Terraform plan..."
terraform plan -out=tfplan

echo ""
read -p "Review the plan above. Continue with apply? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Apply
echo ""
echo "Applying Terraform configuration..."
echo "This may take 15-20 minutes..."
terraform apply tfplan

# Get outputs
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Infrastructure outputs:"
terraform output

echo ""
echo "Next steps:"
echo "1. Build and push Docker images to ECR"
echo "2. Deploy frontend to S3"
echo "3. Configure simulator on EC2"
echo ""
echo "See terraform/DEPLOYMENT.md for detailed instructions"

