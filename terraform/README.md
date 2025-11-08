# AWS Infrastructure as Code

Terraform configuration for deploying the Telematics Insurance System to AWS.

## 📁 Files

- `main.tf` - Main Terraform configuration (all resources)
- `terraform.tfvars.example` - Example variables file
- `.gitignore` - Terraform-specific gitignore
- `deploy.sh` - Main deployment script
- `build-and-push.sh` - Build and push Docker images to ECR
- `deploy-frontend.sh` - Deploy frontend to S3/CloudFront
- `DEPLOYMENT.md` - Complete deployment guide

## 🚀 Quick Start

1. **Configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your settings
   ```

2. **Deploy infrastructure:**
   ```bash
   ./deploy.sh
   ```

3. **Build and push Docker images:**
   ```bash
   ./build-and-push.sh
   ```

4. **Deploy frontend:**
   ```bash
   ./deploy-frontend.sh
   ```

## 📊 Architecture

```
CloudFront → S3 (Frontend)
API Gateway → ALB → ECS Fargate (Backend)
                    ↓
            RDS + ElastiCache
EC2 (Simulator) → SQS → Lambda
```

## 💰 Cost

- **Free Tier (Month 1-12):** $0-5/month
- **After Free Tier:** $30-50/month
- **At Scale (10K users):** $80-150/month

## 📚 Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## ⚠️ Important Notes

1. **NAT Gateway costs ~$32/month** - Consider removing if not needed for private subnet internet access
2. **RDS backups** - Configured for 7-day retention
3. **EC2 Key Pair** - Optional, only needed for SSH access to simulator
4. **Free Tier** - Ensure you're within Free Tier limits to avoid charges

## 🗑️ Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Warning:** This will delete all data including the RDS database!

