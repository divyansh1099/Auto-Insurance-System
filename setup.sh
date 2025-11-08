#!/bin/bash

set -e

echo "========================================="
echo "Telematics Insurance System Setup"
echo "========================================="

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for docker-compose or docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed ($DOCKER_COMPOSE)"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please review and update .env with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/{postgres,kafka,redis,zookeeper}
echo "✅ Data directories created"

# Build and start services
echo ""
echo "Building and starting services..."
echo "This may take several minutes on first run..."
$DOCKER_COMPOSE up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 30

# Check service health
echo ""
echo "Checking service health..."

if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo "✅ Services are running"
else
    echo "❌ Some services failed to start. Check logs with: $DOCKER_COMPOSE logs"
    exit 1
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Services are now running:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Dashboard: http://localhost:3000"
echo "  - Kafka: localhost:9092"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "Next steps:"
echo "  1. Run the data simulator: $DOCKER_COMPOSE exec simulator python telematics_simulator.py"
echo "  2. Train the ML model: $DOCKER_COMPOSE exec backend python /app/ml/train_model.py"
echo "  3. Access the dashboard at http://localhost:3000"
echo ""
echo "Useful commands:"
echo "  - View logs: $DOCKER_COMPOSE logs -f [service_name]"
echo "  - Stop services: $DOCKER_COMPOSE down"
echo "  - Restart services: $DOCKER_COMPOSE restart"
echo ""
