# Free Deployment Guide

Deploy the Auto-Insurance-System to the cloud for free (demo/development purposes).

---

## 🎯 Quick Comparison

| Platform | Best For | Setup Time | Free Tier | Full Stack? |
|----------|----------|------------|-----------|-------------|
| **Railway** | Quickest deploy | 10 min | $5/month credit | ✅ Core services |
| **Render** | Easy multi-service | 15 min | Free (with limits) | ✅ Core services |
| **Fly.io** | Docker-native | 20 min | 3 VMs free | ✅ Core services |
| **Oracle Cloud** | Full control | 30 min | FREE FOREVER | ✅ Everything! |
| **Google Cloud Run** | Serverless | 15 min | Free tier | ⚠️ Backend only |

**Recommendation**:
- **Fastest**: Railway.app (10 min)
- **Best Free Tier**: Oracle Cloud Always Free (can run EVERYTHING)
- **Easiest**: Render.com (click & deploy)

---

## Option 1: Railway.app (Recommended for Quick Start)

### ✅ Pros
- Fastest deployment (10 minutes)
- Auto-deploy from GitHub
- PostgreSQL + Redis included
- Custom domains free
- HTTPS automatic

### ⚠️ Limitations
- $5 credit/month (~500 hours)
- No Kafka (use simplified stack)

### 📋 Setup Steps

#### 1. Prepare Repository

```bash
# Create .railwayignore
cat > .railwayignore <<EOF
data/
*.log
node_modules/
.git/
tests/
docs/
EOF
```

#### 2. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize
railway init

# Deploy
railway up
```

#### 3. Add Services via Dashboard

1. Go to https://railway.app/dashboard
2. Click your project
3. Add **PostgreSQL** service
4. Add **Redis** service
5. Add **Backend** service (from GitHub)
6. Add **Frontend** service (from GitHub)

#### 4. Configure Environment Variables

In Railway dashboard, set for **Backend** service:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
SECRET_KEY=your-secret-key-here
KAFKA_ENABLED=false
```

#### 5. Deploy

```bash
railway up
```

**Done!** Your app is live at `https://your-project.railway.app`

---

## Option 2: Render.com (Best Free Option)

### ✅ Pros
- Completely free (with cold starts)
- PostgreSQL + Redis included
- Auto-deploy from GitHub
- No credit card required

### ⚠️ Limitations
- Services spin down after 15 min (cold start ~30s)
- PostgreSQL free tier expires after 90 days
- No Kafka support

### 📋 Setup Steps

#### 1. Create `render.yaml`

Already created at: `render.yaml` (see below)

#### 2. Push to GitHub

```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

#### 3. Connect to Render

1. Go to https://render.com
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Select `render.yaml`
5. Click "Apply"

**Done!** Render will deploy everything automatically.

### render.yaml

```yaml
services:
  # Backend API
  - type: web
    name: telematics-backend
    env: docker
    dockerfilePath: ./src/backend/Dockerfile
    plan: free
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: telematics-db
          property: connectionString
      - key: REDIS_HOST
        fromService:
          type: redis
          name: telematics-redis
          property: host
      - key: REDIS_PORT
        fromService:
          type: redis
          name: telematics-redis
          property: port
      - key: SECRET_KEY
        generateValue: true
      - key: KAFKA_ENABLED
        value: false
    healthCheckPath: /health

  # Frontend
  - type: web
    name: telematics-frontend
    env: static
    buildCommand: cd src/frontend && npm install && npm run build
    staticPublishPath: ./src/frontend/build
    plan: free
    envVars:
      - key: REACT_APP_API_URL
        fromService:
          type: web
          name: telematics-backend
          property: url

databases:
  # PostgreSQL
  - name: telematics-db
    databaseName: telematics
    plan: free

  # Redis
  - name: telematics-redis
    plan: free
```

---

## Option 3: Oracle Cloud Always Free (Best for Full Stack)

### ✅ Pros
- **FREE FOREVER** (not a trial)
- **4 ARM VMs with 24GB RAM total!**
- Can run EVERYTHING including Kafka
- 200GB storage
- 10TB egress/month

### ⚠️ Limitations
- More setup required (30 minutes)
- Need to manage VM yourself

### 📋 Setup Steps

#### 1. Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Sign up (credit card required but NOT charged)
3. Verify account

#### 2. Create VM Instance

1. In Oracle Console, go to **Compute** → **Instances**
2. Click **Create Instance**
3. Select:
   - **Image**: Ubuntu 22.04
   - **Shape**: Ampere (ARM) - VM.Standard.A1.Flex
   - **OCPU**: 4 (max free)
   - **Memory**: 24GB (max free)
   - **Boot Volume**: 200GB
4. Download SSH key
5. Click **Create**

#### 3. Configure Firewall

```bash
# In Oracle Console, add Ingress Rules:
# Port 80 (HTTP)
# Port 443 (HTTPS)
# Port 8000 (Backend)
# Port 3000 (Frontend)
```

#### 4. SSH into VM

```bash
# Use the downloaded SSH key
ssh -i ~/.ssh/oracle-key ubuntu@<your-vm-ip>
```

#### 5. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Install Git
sudo apt install git -y

# Reboot for docker group
sudo reboot
```

#### 6. Deploy Application

```bash
# SSH back in after reboot
ssh -i ~/.ssh/oracle-key ubuntu@<your-vm-ip>

# Clone repository
git clone <your-repo-url>
cd Auto-Insurance-System

# Create .env file
cat > .env <<EOF
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=$(openssl rand -hex 32)
KAFKA_ENABLED=true
EOF

# Start services
docker compose up -d

# Check status
docker compose ps
```

#### 7. Configure Ubuntu Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp
sudo ufw enable
```

#### 8. Set Up Domain (Optional)

Use a free domain from:
- https://www.freenom.com
- https://freedns.afraid.org

Point A record to your VM IP.

**Done!** Your full stack is running on Oracle Cloud FREE FOREVER!

---

## Option 4: Fly.io (Docker-Native)

### ✅ Pros
- Great Docker support
- Global edge deployment
- 3 VMs free
- Good for microservices

### ⚠️ Limitations
- 256MB RAM per VM (need optimization)
- 3GB storage total

### 📋 Setup Steps

#### 1. Install Fly CLI

```bash
# Mac/Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

#### 2. Login

```bash
fly auth login
```

#### 3. Create `fly.toml`

```toml
app = "telematics-insurance"

[build]
  dockerfile = "src/backend/Dockerfile"

[env]
  PORT = "8000"
  KAFKA_ENABLED = "false"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

#### 4. Create PostgreSQL

```bash
fly postgres create --name telematics-db
```

#### 5. Attach Database

```bash
fly postgres attach telematics-db
```

#### 6. Deploy

```bash
fly deploy
```

**Done!** App is live at `https://your-app.fly.dev`

---

## Simplified Deployment (No Kafka/Zookeeper)

For free tiers that don't support full Docker Compose, use the simplified version:

### Use `docker-compose.demo.yml`

This removes:
- Kafka
- Zookeeper
- Prometheus (can add to backend metrics endpoint)

Core services remain:
- ✅ Backend (FastAPI)
- ✅ Frontend (React)
- ✅ PostgreSQL
- ✅ Redis

### Deploy Simplified Version

```bash
# Use demo compose file
docker compose -f docker-compose.demo.yml up -d
```

### Set Environment Variable

In your backend code, check:
```python
# app/config.py
KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
```

---

## 💰 Cost Comparison

| Platform | Monthly Cost | Limitations | Best For |
|----------|--------------|-------------|----------|
| Railway | $5 credit | 500 hrs/month | Quick demos |
| Render | FREE | Cold starts | Portfolio |
| Fly.io | FREE | 256MB RAM | Microservices |
| Oracle Cloud | **FREE FOREVER** | None! | Full production |
| Heroku | $7/dyno | Min 2 dynos | Paid only |

---

## 🎯 Recommendations

### For Quick Demo (10 minutes)
→ **Railway.app**

### For Portfolio/Resume (free forever)
→ **Render.com** (accept cold starts)

### For Learning/Full Stack (free forever, best specs)
→ **Oracle Cloud Always Free**

### For Production Later
→ Start with Oracle Cloud, migrate to AWS/GCP when needed

---

## 📝 Next Steps After Deployment

1. **Set up monitoring**
   - Use Prometheus (if available)
   - Set up logging
   - Configure alerts

2. **Secure your deployment**
   - Change default passwords
   - Set up HTTPS
   - Configure CORS properly

3. **Optimize for cloud**
   - Enable caching (Redis)
   - Add health checks
   - Configure auto-scaling

4. **Custom domain** (optional)
   - Free: Freenom, FreeDNS
   - Paid: Namecheap ($8/year)

---

## 🆘 Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs -f

# Check resources
docker stats
```

### Out of memory
```bash
# Use demo compose (lighter)
docker compose -f docker-compose.demo.yml up

# Or increase VM RAM (Oracle Cloud)
```

### Database connection issues
```bash
# Check if postgres is ready
docker compose exec postgres pg_isready

# Reset database
docker compose down -v
docker compose up -d
```

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [Oracle Cloud Free Tier](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)

---

**Questions?** Check the troubleshooting section or review platform-specific docs above.
