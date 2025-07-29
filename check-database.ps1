# Check Genomics Platform Database Status
# This script verifies the database connection and shows data counts

Write-Host "🔍 Checking Genomics Platform Database Status..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if PostgreSQL container is running
$postgresStatus = docker ps --filter "name=genomics_postgres" --format "table {{.Names}}\t{{.Status}}"
if ($postgresStatus -like "*genomics_postgres*") {
    Write-Host "✅ PostgreSQL container is running" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL container is not running" -ForegroundColor Red
    Write-Host "Run: .\start-services.ps1" -ForegroundColor Yellow
    exit 1
}

# Test database connection
Write-Host "`n🔗 Testing Database Connection..." -ForegroundColor Yellow
try {
    $testQuery = "SELECT version();"
    $result = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $testQuery
    if ($result -like "*PostgreSQL*") {
        Write-Host "✅ Database connection successful!" -ForegroundColor Green
        Write-Host $result -ForegroundColor Gray
    } else {
        Write-Host "❌ Database connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Database connection failed" -ForegroundColor Red
    exit 1
}

# Check database schema
Write-Host "`n📋 Database Schema:" -ForegroundColor Yellow
try {
    $tablesQuery = "\dt"
    $tables = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $tablesQuery
    Write-Host $tables -ForegroundColor Gray
} catch {
    Write-Host "❌ Error checking database schema" -ForegroundColor Red
}

# Check data counts
Write-Host "`n📊 Data Counts:" -ForegroundColor Yellow

try {
    # Datasets count
    $datasetsQuery = "SELECT COUNT(*) as dataset_count FROM datasets;"
    $datasets = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $datasetsQuery
    Write-Host "📋 Datasets: $datasets" -ForegroundColor Cyan
    
    # Samples count
    $samplesQuery = "SELECT COUNT(*) as sample_count FROM samples;"
    $samples = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $samplesQuery
    Write-Host "🧬 Samples: $samples" -ForegroundColor Cyan
    
    # Variants count
    $variantsQuery = "SELECT COUNT(*) as variant_count FROM variants;"
    $variants = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $variantsQuery
    Write-Host "🔬 Variants: $variants" -ForegroundColor Cyan
    
    # Gene expression count
    $expressionQuery = "SELECT COUNT(*) as expression_count FROM gene_expression;"
    $expression = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $expressionQuery
    Write-Host "🧪 Gene Expression: $expression" -ForegroundColor Cyan
    
    # Drug targets count
    $drugsQuery = "SELECT COUNT(*) as drug_count FROM drug_targets;"
    $drugs = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $drugsQuery
    Write-Host "💊 Drug Targets: $drugs" -ForegroundColor Cyan
    
    # Literature entities count
    $literatureQuery = "SELECT COUNT(*) as literature_count FROM literature_entities;"
    $literature = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $literatureQuery
    Write-Host "📚 Literature Entities: $literature" -ForegroundColor Cyan
    
    # Analysis jobs count
    $jobsQuery = "SELECT COUNT(*) as job_count FROM analysis_jobs;"
    $jobs = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $jobsQuery
    Write-Host "⚙️ Analysis Jobs: $jobs" -ForegroundColor Cyan
    
    # Model predictions count
    $predictionsQuery = "SELECT COUNT(*) as prediction_count FROM model_predictions;"
    $predictions = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $predictionsQuery
    Write-Host "🤖 Model Predictions: $predictions" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error checking data counts: $($_.Exception.Message)" -ForegroundColor Red
}

# Show dataset summary
Write-Host "`n📈 Dataset Summary:" -ForegroundColor Yellow
try {
    $summaryQuery = "SELECT name, source, total_samples, total_variants, created_at FROM datasets ORDER BY created_at DESC;"
    $summary = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $summaryQuery
    Write-Host $summary -ForegroundColor Gray
} catch {
    Write-Host "❌ Error getting dataset summary" -ForegroundColor Red
}

# Database size information
Write-Host "`n💾 Database Size:" -ForegroundColor Yellow
try {
    $sizeQuery = "SELECT pg_size_pretty(pg_database_size('genomics_platform')) as database_size;"
    $size = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $sizeQuery
    Write-Host $size -ForegroundColor Gray
} catch {
    Write-Host "❌ Error getting database size" -ForegroundColor Red
}

Write-Host "`n✅ Database status check completed!" -ForegroundColor Green 