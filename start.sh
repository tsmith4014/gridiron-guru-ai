#!/bin/bash

echo "🏈 Starting Gridiron Guru AI..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

echo "🚀 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "🎉 Gridiron Guru AI is now running!"
echo ""
echo "🌐 Access your application at:"
echo "   • Main App: http://localhost:8000"
echo "   • Draft Assistant: http://localhost:8000/draft"
echo "   • Legacy Version: http://localhost:8000/legacy"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
