#!/bin/bash

set -e

echo "🚀 Setting up NexusAgent..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed."; exit 1; }

# Create necessary directories
mkdir -p workspaces
mkdir -p models/configs

# Copy environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file - please configure it"
fi

# Build and start services
echo "📦 Building Docker services..."
docker-compose -f deployment/docker/docker-compose.yml build

echo "🚀 Starting NexusAgent..."
docker-compose -f deployment/docker/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 10

# Pull default models (optional)
echo "📥 Pulling default models..."
docker exec -it nexusagent-ollama-1 ollama pull llama4:70b 2>/dev/null || true

echo ""
echo "✅ NexusAgent is running!"
echo ""
echo "📋 Access points:"
echo "   Dashboard:  http://localhost:3000"
echo "   API:        http://localhost:8000"
echo "   Ollama:     http://localhost:11434"
echo ""
echo "📖 Next steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Create your first agent"
echo "   3. Execute your first task"
echo ""
echo "🛑 To stop: docker-compose -f deployment/docker/docker-compose.yml down"
