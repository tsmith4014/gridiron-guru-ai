#!/bin/bash

# Gridiron Guru AI - Fantasy Football Draft Assistant
# Quick start script for spinning up the application

set -e  # Exit on any error

echo "🏈 Gridiron Guru AI - Fantasy Football Draft Assistant"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
print_status "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker is running"

# Check if docker-compose is available
print_status "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install Docker Compose and try again."
    exit 1
fi
print_success "Docker Compose is available"

echo ""

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Build and start the application
print_status "Building Docker images..."
docker-compose build --no-cache

print_status "Starting services..."
docker-compose up -d

echo ""
print_status "Waiting for services to be ready..."
sleep 15

# Check if services are running
print_status "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo ""
    print_success "Application is now running!"
    echo ""
    echo "🌐 Frontend: http://localhost:8000"
    echo "🔌 API: http://localhost:8000/api"
    echo "🗄️  Database: localhost:5432 (draft_db)"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   View backend logs: docker-compose logs -f backend"
    echo "   View database logs: docker-compose logs -f db"
    echo "   Stop services: docker-compose down"
    echo "   Restart services: docker-compose restart"
    echo ""
    echo "🏈 Happy drafting!"
    echo ""
    print_status "Opening frontend in browser..."
    if command -v open &> /dev/null; then
        open http://localhost:8000
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000
    else
        print_warning "Please manually open http://localhost:8000 in your browser"
    fi
else
    print_error "Failed to start services. Checking logs..."
    docker-compose logs
    exit 1
fi
