#!/bin/bash

# Gridiron Guru AI - Fantasy Football Draft Assistant
# Quick start script for spinning up the application

set -e # Exit on any error

echo "🏈 Gridiron Guru AI - Fantasy Football Draft Assistant"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
	echo "❌ Docker is not running. Please start Docker and try again."
	exit 1
fi
echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &>/dev/null; then
	echo "❌ docker-compose is not installed. Please install Docker Compose and try again."
	exit 1
fi
echo "✅ Docker Compose is available"

echo ""
echo "🚀 Building and starting Gridiron Guru AI..."
echo ""

# Build and start the services
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
	echo "✅ Services are running successfully!"
	echo ""
	echo "🌐 Gridiron Guru AI is now available at:"
	echo "   http://localhost:8001"
	echo ""
	echo "📊 Database is available at:"
	echo "   localhost:5433"
	echo ""
	echo "🔧 To view logs: docker-compose logs -f"
	echo "🛑 To stop: docker-compose down"
	echo ""

	# Try to open the browser (macOS)
	if command -v open &>/dev/null; then
		echo "🌐 Opening browser..."
		open http://localhost:8001
	fi
else
	echo "❌ Services failed to start. Check logs with: docker-compose logs"
	exit 1
fi
