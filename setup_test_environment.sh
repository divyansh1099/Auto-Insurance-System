#!/bin/bash
# Setup Test Environment
# This script prepares your environment for running comprehensive tests

set -e  # Exit on error

echo "=================================="
echo "Test Environment Setup"
echo "=================================="
echo ""

# Check if running in project directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

echo "1️⃣  Starting Docker services..."
docker compose up -d
echo "   ✅ Services started"
echo ""

echo "2️⃣  Waiting for PostgreSQL to be ready (30 seconds)..."
sleep 30
echo "   ✅ PostgreSQL should be ready"
echo ""

echo "3️⃣  Checking if database role exists..."
if docker compose exec -T postgres psql -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='insurance_user'" | grep -q 1; then
    echo "   ✅ Database role 'insurance_user' already exists"
else
    echo "   Creating database role..."
    docker compose exec -T postgres psql -U postgres -c "CREATE USER insurance_user WITH PASSWORD 'insurance_pass';"
    echo "   ✅ Database role created"
fi
echo ""

echo "4️⃣  Checking if database exists..."
if docker compose exec -T postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw telematics_db; then
    echo "   ✅ Database 'telematics_db' already exists"
else
    echo "   Creating database..."
    docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE telematics_db OWNER insurance_user;"
    echo "   ✅ Database created"
fi
echo ""

echo "5️⃣  Granting database privileges..."
docker compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE telematics_db TO insurance_user;"
docker compose exec -T postgres psql -U postgres -d telematics_db -c "GRANT ALL ON SCHEMA public TO insurance_user;"
docker compose exec -T postgres psql -U postgres -d telematics_db -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO insurance_user;"
echo "   ✅ Privileges granted"
echo ""

echo "6️⃣  Checking if tables exist..."
TABLE_COUNT=$(docker compose exec -T postgres psql -U insurance_user -d telematics_db -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -gt "0" ]; then
    echo "   ✅ Database has $TABLE_COUNT tables"
else
    echo "   ⚠️  No tables found. You may need to run migrations:"
    echo "      docker compose exec backend alembic upgrade head"
    echo "   Or initialize the database with sample data"
fi
echo ""

echo "7️⃣  Checking if Phase 1 indexes exist..."
INDEX_COUNT=$(docker compose exec -T postgres psql -U insurance_user -d telematics_db -tAc "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public' AND indexname LIKE 'idx_%';" 2>/dev/null || echo "0")

if [ "$INDEX_COUNT" -ge "20" ]; then
    echo "   ✅ Phase 1 indexes exist ($INDEX_COUNT indexes)"
else
    echo "   ⚠️  Only $INDEX_COUNT indexes found (expected 20+)"
    echo "   Run Phase 1 migration:"
    echo "      docker compose exec postgres psql -U insurance_user -d telematics_db -f /docker-entrypoint-initdb.d/001_add_performance_indexes.sql"
fi
echo ""

echo "8️⃣  Checking admin user..."
ADMIN_EXISTS=$(docker compose exec -T backend python -c "
from app.models.database import SessionLocal
from app.models.database import User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
print('yes' if admin else 'no')
" 2>/dev/null || echo "no")

if [ "$ADMIN_EXISTS" = "yes" ]; then
    echo "   ✅ Admin user exists"
else
    echo "   Creating admin user..."
    docker compose exec -T backend python -c "
from app.models.database import SessionLocal
from app.models.database import User
from app.utils.auth import get_password_hash

db = SessionLocal()
admin = User(
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created')
" 2>/dev/null && echo "   ✅ Admin user created" || echo "   ⚠️  Could not create admin user"
fi
echo ""

echo "9️⃣  Testing backend API..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend API is accessible"
else
    echo "   ⚠️  Backend API not accessible"
    echo "   Check logs: docker compose logs backend"
fi
echo ""

echo "🔟  Checking backend dependencies..."
# Check if slowapi is installed in backend container
if docker compose exec -T backend python -c "import slowapi" 2>/dev/null; then
    echo "   ✅ Backend dependencies OK (slowapi installed)"
else
    echo "   ⚠️  Missing slowapi in backend container"
    echo "   Installing slowapi..."
    docker compose exec -T backend pip install slowapi 2>/dev/null && echo "   ✅ slowapi installed" || echo "   ⚠️  Failed to install slowapi"
    echo "   Restarting backend..."
    docker compose restart backend
    sleep 10
fi
echo ""

echo "1️⃣1️⃣  Installing Python test dependencies ON HOST..."
echo "   These packages must be installed on YOUR MACHINE (not in Docker):"
echo ""
if pip install -q -r requirements-test.txt 2>/dev/null; then
    echo "   ✅ Test dependencies installed (requests, psycopg2-binary)"
else
    echo "   ⚠️  Could not install dependencies automatically"
    echo ""
    echo "   Please install manually:"
    echo "   pip install -r requirements-test.txt"
    echo "   # OR:"
    echo "   pip install requests psycopg2-binary"
fi
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Run environment check to verify:"
echo "  python check_environment.py"
echo ""
echo "If all checks pass, run tests:"
echo "  python run_all_tests.py"
echo ""
