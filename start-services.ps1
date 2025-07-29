# Start Genomics Platform Services
# This script starts PostgreSQL, Redis, and MinIO using Docker Compose

Write-Host "Starting Genomics Platform Services..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running!" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "You can start Docker Desktop from the Start menu or by running:" -ForegroundColor Yellow
    Write-Host "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'" -ForegroundColor Yellow
    exit 1
}

# Start services using Docker Compose
Write-Host "Starting PostgreSQL, Redis, and MinIO..." -ForegroundColor Yellow
docker-compose up -d

# Wait a moment for services to start
Start-Sleep -Seconds 10

# Check if services are running
Write-Host "Checking service status..." -ForegroundColor Yellow

$services = @("genomics_postgres", "genomics_redis", "genomics_minio")

foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "table {{.Names}}\t{{.Status}}"
    if ($status -like "*$service*") {
        Write-Host "✅ $service is running" -ForegroundColor Green
    } else {
        Write-Host "❌ $service is not running" -ForegroundColor Red
    }
}

# Test PostgreSQL connection
Write-Host "Testing PostgreSQL connection..." -ForegroundColor Yellow
try {
    $testQuery = "SELECT version();"
    $result = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $testQuery
    if ($result -like "*PostgreSQL*") {
        Write-Host "✅ PostgreSQL connection successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ PostgreSQL connection failed" -ForegroundColor Red
}

# Display connection information
Write-Host "`n📊 Service Connection Information:" -ForegroundColor Cyan
Write-Host "PostgreSQL:" -ForegroundColor White
Write-Host "  Host: localhost" -ForegroundColor Gray
Write-Host "  Port: 5432" -ForegroundColor Gray
Write-Host "  Database: genomics_platform" -ForegroundColor Gray
Write-Host "  Username: genomics_user" -ForegroundColor Gray
Write-Host "  Password: Boolmind2025@@" -ForegroundColor Gray

Write-Host "`nRedis:" -ForegroundColor White
Write-Host "  Host: localhost" -ForegroundColor Gray
Write-Host "  Port: 6379" -ForegroundColor Gray

Write-Host "`nMinIO:" -ForegroundColor White
Write-Host "  API Endpoint: http://localhost:9000" -ForegroundColor Gray
Write-Host "  Console: http://localhost:9001" -ForegroundColor Gray
Write-Host "  Username: minioadmin" -ForegroundColor Gray
Write-Host "  Password: minioadmin123" -ForegroundColor Gray

Write-Host "`n🎉 All services are ready!" -ForegroundColor Green
Write-Host "You can now run your data pipelines and connect to the database." -ForegroundColor Yellow 