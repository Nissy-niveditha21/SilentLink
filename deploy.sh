#!/bin/bash
# Deployment script for SilentLink

set -e

echo "🚀 SilentLink Deployment Script"
echo "================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Check for production environment file
if [ ! -f .env.production ]; then
    echo "⚠️  Warning: .env.production file not found."
    echo "Creating from example..."
    if [ -f .env.production.example ]; then
        cp .env.production.example .env.production
        echo "✅ Created .env.production from example"
        echo "⚠️  Please edit .env.production with your production values before continuing!"
        exit 1
    else
        echo "❌ .env.production.example not found either."
        exit 1
    fi
fi

# Load production environment variables
export $(grep -v '^#' .env.production | xargs)

# Validate SECRET_KEY
if [ "$SECRET_KEY" = "generate-a-strong-random-secret-key-here-minimum-32-chars" ]; then
    echo "❌ SECRET_KEY is still the default value. Please set a strong secret key in .env.production"
    exit 1
fi

echo "✅ Environment validation passed"
echo "📦 Building Docker image..."

# Build the Docker image
docker-compose build

echo "🚀 Starting SilentLink in production mode..."
echo "📊 The application will be available at: http://localhost:8000"
echo "📝 Logs will be displayed below. Press Ctrl+C to stop."

# Start the application
docker-compose up -d

echo "✅ SilentLink is now running in the background!"
echo ""
echo "📋 Useful commands:"
echo "   docker-compose logs -f      # View logs"
echo "   docker-compose ps           # Check status"
echo "   docker-compose down         # Stop the application"
echo "   docker-compose restart      # Restart the application"
echo ""
echo "🔧 To update the application:"
echo "   1. Pull latest changes"
echo "   2. Run: docker-compose build --no-cache"
echo "   3. Run: docker-compose up -d"
echo ""
echo "🎉 Deployment complete!"