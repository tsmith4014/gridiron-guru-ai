#!/bin/bash

echo "🚀 Starting Enhanced Fantasy Draft Assistant with ML..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🎯 Your Enhanced Fantasy Draft Assistant is ready!"
echo "🌐 Access it at: http://localhost:8000"
echo ""
echo "📊 API Documentation: http://localhost:8000/docs"
echo "📚 Interactive API: http://localhost:8000/redoc"
echo ""
echo "🛑 To stop the services, run: docker-compose down"
echo "📝 To view logs, run: docker-compose logs -f"
