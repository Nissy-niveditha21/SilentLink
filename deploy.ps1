# SilentLink Deployment Script for Windows PowerShell

Write-Host "🚀 SilentLink Deployment Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop for Windows first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed." -ForegroundColor Red
    exit 1
}

# Check for production environment file
if (-not (Test-Path ".env.production")) {
    Write-Host "⚠️  Warning: .env.production file not found." -ForegroundColor Yellow
    Write-Host "Creating from example..." -ForegroundColor Yellow
    if (Test-Path ".env.production.example") {
        Copy-Item ".env.production.example" ".env.production"
        Write-Host "✅ Created .env.production from example" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env.production with your production values before continuing!" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "❌ .env.production.example not found either." -ForegroundColor Red
        exit 1
    }
}

# Read and validate SECRET_KEY
$envContent = Get-Content ".env.production" -Raw
if ($envContent -match "SECRET_KEY=generate-a-strong-random-secret-key-here-minimum-32-chars") {
    Write-Host "❌ SECRET_KEY is still the default value. Please set a strong secret key in .env.production" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment validation passed" -ForegroundColor Green
Write-Host "📦 Building Docker image..." -ForegroundColor Cyan

# Build the Docker image
docker-compose build

Write-Host "🚀 Starting SilentLink in production mode..." -ForegroundColor Cyan
Write-Host "📊 The application will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "📝 Starting application in background..." -ForegroundColor Yellow

# Start the application
docker-compose up -d

Write-Host "✅ SilentLink is now running in the background!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f      # View logs" -ForegroundColor Gray
Write-Host "   docker-compose ps           # Check status" -ForegroundColor Gray
Write-Host "   docker-compose down         # Stop the application" -ForegroundColor Gray
Write-Host "   docker-compose restart      # Restart the application" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 To update the application:" -ForegroundColor Cyan
Write-Host "   1. Pull latest changes" -ForegroundColor Gray
Write-Host "   2. Run: docker-compose build --no-cache" -ForegroundColor Gray
Write-Host "   3. Run: docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green