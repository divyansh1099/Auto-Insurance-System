# AWS Deployment Guide

Complete guide for deploying the Telematics Insurance System to AWS.

## 📋 Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```
3. **Terraform** >= 1.0 installed
   ```bash
   terraform version
   ```
4. **Docker** installed (for building/pushing images)
5. **Docker Compose** (for local testing)

## 🏗️ Architecture Overview

```
┌─────────────────┐
│  CloudFront CDN │  ← Frontend (React)
└────────┬────────┘
         │
    ┌────▼────┐
    │ S3 Bucket│
    └─────────┘

┌─────────────────┐
│  API Gateway    │  ← REST API
└────────┬────────┘
         │
    ┌────▼────┐
    │   ALB   │
    └─────────┘
         │
    ┌────▼──────────────┐
    │  ECS Fargate      │  ← Backend (FastAPI)
    │  (Backend Service)│
    └───────────────────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼────┐              ┌─────▼─────┐
│  RDS   │              │ ElastiCache│
│Postgres│              │   Redis    │
└────────┘              └────────────┘

┌─────────────────┐
│  EC2 t3.micro   │  ← Simulator
└─────────────────┘
         │
    ┌────▼────┐
    │   SQS   │  ← Event Queue
    └─────────┘
```

## 🚀 Step-by-Step Deployment

### Step 1: Configure Variables

1. Copy the example variables file:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your settings:
   ```hcl
   aws_region   = "us-east-1"
   environment  = "production"
   project_name = "telematics-insurance"
   ```

### Step 2: Deploy Infrastructure

Run the deployment script:
```bash
cd terraform
./deploy.sh
```

Or manually:
```bash
terraform init
terraform plan
terraform apply
```

**Expected Time:** 15-20 minutes

**What gets created:**
- VPC with public/private subnets
- RDS PostgreSQL (db.t3.micro)
- ElastiCache Redis (cache.t3.micro)
- ECS Cluster with Fargate
- Application Load Balancer
- API Gateway
- S3 bucket for frontend
- CloudFront distribution
- SQS queue for events
- EC2 instance for simulator
- ECR repositories for Docker images

### Step 3: Build and Push Docker Images

After infrastructure is deployed, get the ECR repository URLs:
```bash
terraform output ecr_backend_repository_url
terraform output ecr_simulator_repository_url
```

#### Backend Image

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build image
cd ..
docker build -t telematics-insurance/backend:latest ./backend

# Tag for ECR
ECR_URL=$(cd terraform && terraform output -raw ecr_backend_repository_url)
docker tag telematics-insurance/backend:latest ${ECR_URL}:latest

# Push to ECR
docker push ${ECR_URL}:latest
```

#### Simulator Image

```bash
ECR_SIM_URL=$(cd terraform && terraform output -raw ecr_simulator_repository_url)
docker build -t telematics-insurance/simulator:latest ./simulator
docker tag telematics-insurance/simulator:latest ${ECR_SIM_URL}:latest
docker push ${ECR_SIM_URL}:latest
```

### Step 4: Update ECS Service

After pushing images, update the ECS service to use the new image:

```bash
# Get cluster and service names
CLUSTER=$(cd terraform && terraform output -raw project_name)-cluster
SERVICE=$(cd terraform && terraform output -raw project_name)-backend-service

# Force new deployment
aws ecs update-service \
  --cluster ${CLUSTER} \
  --service ${SERVICE} \
  --force-new-deployment \
  --region us-east-1
```

### Step 5: Deploy Frontend

#### Build Frontend

```bash
cd frontend
npm install
npm run build
```

#### Upload to S3

```bash
# Get bucket name from Terraform output
BUCKET_NAME=$(cd terraform && terraform output -raw project_name)-frontend-$(aws sts get-caller-identity --query Account --output text)

# Upload build files
aws s3 sync dist/ s3://${BUCKET_NAME}/ --delete

# Enable website hosting (if not already done)
aws s3 website s3://${BUCKET_NAME}/ --index-document index.html --error-document index.html
```

#### Invalidate CloudFront Cache

```bash
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='telematics-insurance-frontend-cdn'].Id" --output text)
aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths "/*"
```

### Step 6: Configure Simulator on EC2

1. **SSH into EC2 instance:**
   ```bash
   EC2_IP=$(cd terraform && terraform output -raw ec2_simulator_public_ip)
   ssh -i your-key.pem ec2-user@${EC2_IP}
   ```

2. **Install Docker Compose:**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Clone repository and configure:**
   ```bash
   git clone <your-repo-url>
   cd Auto\ Insurance\ System
   
   # Create .env file with AWS endpoints
   cat > .env << EOF
   DATABASE_URL=postgresql://insurance_user:PASSWORD@RDS_ENDPOINT/telematics_db
   REDIS_HOST=REDIS_ENDPOINT
   REDIS_PORT=6379
   SQS_QUEUE_URL=SQS_QUEUE_URL
   EOF
   ```

4. **Run simulator:**
   ```bash
   docker compose up -d simulator
   ```

## 🔍 Verify Deployment

### Check Services

1. **ECS Service:**
   ```bash
   aws ecs describe-services \
     --cluster telematics-insurance-cluster \
     --services telematics-insurance-backend-service
   ```

2. **RDS:**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier telematics-insurance-db
   ```

3. **Frontend:**
   ```bash
   # Get CloudFront URL
   terraform output cloudfront_url
   # Open in browser
   ```

4. **API:**
   ```bash
   # Get API Gateway URL
   terraform output api_gateway_url
   # Test health endpoint
   curl $(terraform output -raw api_gateway_url)/health
   ```

## 💰 Cost Optimization

### Free Tier (First 12 Months)

- **RDS:** 750 hours/month of db.t3.micro
- **EC2:** 750 hours/month of t3.micro
- **ElastiCache:** 750 hours/month of cache.t3.micro
- **S3:** 5GB storage, 20,000 GET requests
- **CloudFront:** 50GB data transfer out
- **API Gateway:** 1M requests/month
- **Lambda:** 1M requests/month, 400,000 GB-seconds

### Estimated Monthly Costs

**Month 1-12 (Free Tier):** $0-5/month
- Only data transfer and storage beyond free tier

**After Free Tier:** $30-50/month
- RDS: ~$15/month
- EC2: ~$8/month
- ElastiCache: ~$12/month
- NAT Gateway: ~$32/month (consider removing if not needed)
- ALB: ~$16/month
- S3/CloudFront: ~$2/month

**At Scale (10K users):** $80-150/month

## 🔧 Troubleshooting

### ECS Service Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster telematics-insurance-cluster \
  --services telematics-insurance-backend-service \
  --query 'services[0].events[:5]'

# Check task logs
aws logs tail /ecs/telematics-insurance/backend --follow
```

### Database Connection Issues

1. Check security groups allow traffic from ECS tasks
2. Verify RDS endpoint is correct
3. Check password in ECS task environment variables

### Frontend Not Loading

1. Check S3 bucket policy allows public read
2. Verify CloudFront distribution is deployed
3. Check CORS settings if API calls fail

## 🗑️ Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete all data including RDS database!

## 📚 Additional Resources

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/intro.html)

