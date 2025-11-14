# Data Persistence Guide

## Problem: Data Loss After Docker Restart

**Issue**: All database data (admin users, drivers, trips, etc.) is lost when Docker is shut down and restarted.

**Root Cause**: The current Docker setup uses bind mounts (`./data/postgres`) which can be accidentally deleted or not properly persisted depending on how Docker is stopped.

---

## Quick Fix: Restore Data Now

Run this script to restore your admin user and sample data:

```bash
./restore-data.sh
```

**This script will:**
- ✅ Create admin user (username: `admin`, password: `admin123`)
- ✅ Create test user (username: `user1`, password: `user123`)
- ✅ Insert 7 sample drivers
- ✅ Insert 7 sample vehicles
- ✅ Insert 7 sample devices
- ✅ Insert 7 risk scores
- ✅ Insert 7 premiums
- ✅ Insert 7 sample trips

**Login Credentials After Restore:**
- **Admin**: `admin` / `admin123`
- **Test User**: `user1` / `user123`

---

## Understanding the Issue

### Current Setup (Problematic)

The `docker-compose.yml` uses bind mounts:

```yaml
postgres:
  volumes:
    - ./data/postgres:/var/lib/postgresql/data  # ❌ Bind mount
```

**Problem**: If you run `docker-compose down -v` or delete the `./data/postgres` directory, all data is lost.

### What Happens

1. **First Time**: `docker-compose up`
   - Creates `./data/postgres` directory
   - Runs `init.sql` to create schema (tables only)
   - No data inserted yet

2. **You Add Data**: Via API or manual SQL
   - Data stored in `./data/postgres`

3. **Docker Shutdown**: Various ways to stop
   - `docker-compose stop` → ✅ Data preserved
   - `docker-compose down` → ✅ Data preserved (usually)
   - `docker-compose down -v` → ❌ **DATA DELETED**
   - Deleting `./data/*` manually → ❌ **DATA DELETED**

4. **Restart**: `docker-compose up`
   - Recreates containers
   - `init.sql` runs again (creates tables)
   - No data (empty tables)

---

## Prevention Strategies

### Option 1: Use Docker Named Volumes (Recommended)

**Modify `docker-compose.yml`:**

```yaml
services:
  postgres:
    image: postgres:15
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-insurance_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-insurance_pass}
      POSTGRES_DB: ${POSTGRES_DB:-telematics_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ✅ Named volume
      - ./src/backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U insurance_user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:  # ✅ Docker-managed volume
    driver: local
```

**Benefits:**
- ✅ Data survives `docker-compose down`
- ✅ Data only deleted with explicit `docker-compose down -v`
- ✅ Docker manages volume lifecycle
- ✅ Better performance on some systems

**To apply this change:**

1. Backup current data: `./backup-database.sh` (create if needed)
2. Update `docker-compose.yml`
3. Run `docker-compose down`
4. Run `docker-compose up -d`
5. Restore data: `./restore-data.sh`

### Option 2: Always Use `docker-compose stop` (Current Setup)

If you keep the current bind mount setup:

**Safe Commands:**
```bash
# Stop containers (keeps data)
docker-compose stop

# Start containers
docker-compose start

# Restart containers
docker-compose restart
```

**Dangerous Commands:**
```bash
# Remove containers and networks (usually keeps data, but risky)
docker-compose down

# ❌ NEVER USE - Deletes volumes
docker-compose down -v

# ❌ NEVER DO - Deletes data
rm -rf ./data/postgres
```

### Option 3: Add Data Initialization to init.sql

**Modify `src/backend/init.sql` to include:**

```sql
-- At the end of init.sql, add:

-- Insert default admin user
INSERT INTO users (username, email, password_hash, is_active, is_admin, created_at)
VALUES (
    'admin',
    'admin@insurance.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNv0C8J9Fi', -- admin123
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP
)
ON CONFLICT (username) DO NOTHING;

-- Add other default data...
```

**Benefits:**
- ✅ Admin user automatically created on first start
- ✅ No manual restoration needed
- ⚠️ Still need to run restore script for sample data

---

## Database Backup & Restore

### Manual Backup

```bash
# Create backup
docker exec postgres pg_dump -U insurance_user telematics_db > backup.sql

# With timestamp
docker exec postgres pg_dump -U insurance_user telematics_db > backup-$(date +%Y%m%d-%H%M%S).sql
```

### Manual Restore

```bash
# Restore from backup
docker exec -i postgres psql -U insurance_user -d telematics_db < backup.sql
```

### Automated Backup Script

Create `backup-database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

echo "Creating backup: $BACKUP_FILE"
docker exec postgres pg_dump -U insurance_user telematics_db > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $(du -h $BACKUP_FILE | cut -f1)"
else
    echo "❌ Backup failed"
    exit 1
fi

# Keep only last 10 backups
ls -t $BACKUP_DIR/backup-*.sql | tail -n +11 | xargs rm -f
echo "Cleaned up old backups (keeping latest 10)"
```

Make it executable:
```bash
chmod +x backup-database.sh
```

---

## Data Restoration After Loss

### Step 1: Check Current Status

```bash
# Check if containers are running
docker-compose ps

# Check if database has data
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM users;"
```

### Step 2: Run Restoration Script

```bash
./restore-data.sh
```

### Step 3: Verify Data

```bash
# Check users table
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT username, email, is_admin FROM users;"

# Check drivers count
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM drivers;"

# Check trips count
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM trips;"
```

### Step 4: Test Login

1. Open frontend: http://localhost:3000
2. Login with admin credentials
3. Verify dashboard shows data

---

## Preventing Data Loss: Best Practices

### 1. Never Use `docker-compose down -v`

Unless you specifically want to delete all data.

### 2. Use Named Volumes

See "Option 1" above for configuration.

### 3. Regular Backups

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * /path/to/Auto-Insurance-System/backup-database.sh
```

### 4. Use `.dockerignore`

Prevent accidental deletion of data directory:

Create `.dockerignore`:
```
data/postgres/
data/redis/
data/kafka/
data/zookeeper/
backups/
```

### 5. Add Data Directory to `.gitignore`

Already done, but verify:

```bash
grep "data/" .gitignore
```

Should show:
```
data/
```

### 6. Document Startup Process

Create a `START.md` with safe commands:

```markdown
# Starting the Application

## Safe Startup
docker-compose up -d

## Safe Shutdown
docker-compose stop

## Safe Restart
docker-compose restart

## ⚠️ DANGER - Only if you want to delete ALL data
docker-compose down -v
```

---

## Troubleshooting

### Issue: "role 'insurance_user' does not exist"

**Solution:**
```bash
docker-compose down
docker-compose up -d
# Wait 10 seconds for database initialization
./restore-data.sh
```

### Issue: "relation 'users' does not exist"

**Solution:**
```bash
# Recreate database from init.sql
docker exec -i postgres psql -U insurance_user -d telematics_db < src/backend/init.sql
./restore-data.sh
```

### Issue: "FATAL: database 'telematics_db' does not exist"

**Solution:**
```bash
docker-compose down
rm -rf ./data/postgres  # Start fresh
docker-compose up -d
# Wait 10 seconds
./restore-data.sh
```

### Issue: "Connection refused" to database

**Solution:**
```bash
# Check if PostgreSQL container is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart if needed
docker-compose restart postgres

# Wait for health check to pass
docker-compose ps postgres
# Should show "(healthy)"
```

### Issue: Data exists but can't login

**Solution:**
```bash
# Reset admin password
docker exec -i postgres psql -U insurance_user -d telematics_db <<EOF
UPDATE users
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNv0C8J9Fi'
WHERE username = 'admin';
EOF

# Verify
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT username, is_admin FROM users WHERE username='admin';"
```

---

## Migrating to Named Volumes

If you want to switch from bind mounts to named volumes:

### Step 1: Backup Current Data

```bash
./backup-database.sh
# Or manual backup
docker exec postgres pg_dump -U insurance_user telematics_db > migration-backup.sql
```

### Step 2: Update docker-compose.yml

Replace:
```yaml
- ./data/postgres:/var/lib/postgresql/data
```

With:
```yaml
- postgres_data:/var/lib/postgresql/data
```

Add at the bottom:
```yaml
volumes:
  postgres_data:
    driver: local
```

### Step 3: Recreate Containers

```bash
docker-compose down
docker-compose up -d
```

### Step 4: Restore Data

```bash
./restore-data.sh
# Or restore from backup
docker exec -i postgres psql -U insurance_user -d telematics_db < migration-backup.sql
```

### Step 5: Verify

```bash
# Check data
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM users;"

# Test login at http://localhost:3000
```

---

## Summary

### Current Situation
- ✅ Data restoration script created: `restore-data.sh`
- ⚠️ Using bind mounts (risky for data loss)
- ✅ `init.sql` creates schema but not data

### Immediate Action
```bash
./restore-data.sh
```

### Long-Term Fix (Choose One)

**Option A: Switch to Named Volumes (Recommended)**
- Update `docker-compose.yml`
- More reliable data persistence
- Better for production-like environments

**Option B: Keep Bind Mounts + Be Careful**
- Always use `docker-compose stop` not `down`
- Never use `docker-compose down -v`
- Regular backups with `backup-database.sh`

**Option C: Auto-Initialize Data**
- Modify `init.sql` to include admin user
- Still need restore script for sample data

### Recommended: Option A + Regular Backups

1. Switch to named volumes
2. Set up automated daily backups
3. Keep `restore-data.sh` for quick recovery
4. Document safe startup/shutdown procedures

---

## Quick Reference

```bash
# Restore data (after loss)
./restore-data.sh

# Safe shutdown
docker-compose stop

# Safe startup
docker-compose start

# Full restart (keeps data)
docker-compose restart

# Create backup
docker exec postgres pg_dump -U insurance_user telematics_db > backup.sql

# Restore from backup
docker exec -i postgres psql -U insurance_user -d telematics_db < backup.sql

# Check data status
docker exec postgres psql -U insurance_user -d telematics_db -c "SELECT COUNT(*) FROM users;"
```

---

**Default Credentials After Restore:**
- Admin: `admin` / `admin123`
- Test User: `user1` / `user123`

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
