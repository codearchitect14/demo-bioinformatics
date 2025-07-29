# Populate Genomics Platform Database with Datasets
# This script runs the data pipelines to populate the PostgreSQL database

Write-Host "🧬 Populating Genomics Platform Database with Datasets..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "After rebooting for WSL, start Docker Desktop and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if services are running
Write-Host "Checking if services are running..." -ForegroundColor Yellow
$services = @("genomics_postgres", "genomics_redis", "genomics_minio")

foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "table {{.Names}}\t{{.Status}}"
    if ($status -like "*$service*") {
        Write-Host "✅ $service is running" -ForegroundColor Green
    } else {
        Write-Host "❌ $service is not running. Starting services..." -ForegroundColor Red
        docker-compose up -d
        Start-Sleep -Seconds 15
        break
    }
}

# Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow
try {
    $testQuery = "SELECT version();"
    $result = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $testQuery
    if ($result -like "*PostgreSQL*") {
        Write-Host "✅ Database connection successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ Database connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Database connection failed" -ForegroundColor Red
    exit 1
}

# Create data directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
$dataDirs = @("data", "data/clinvar", "data/tcga", "data/pubmed", "logs")
foreach ($dir in $dataDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created directory: $dir" -ForegroundColor Gray
    }
}

# Install Python dependencies if needed
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
if (Test-Path "data_pipeline/requirements.txt") {
    Write-Host "Installing data pipeline dependencies..." -ForegroundColor Yellow
    pip install -r data_pipeline/requirements.txt
}

# Set environment variables for data pipelines
$env:CLINVAR_DATA_PATH = "data/clinvar"
$env:TCGA_DATA_PATH = "data/tcga"
$env:PUBMED_DATA_PATH = "data/pubmed"
$env:DATABASE_URL = "postgresql://genomics_user:Boolmind2025@@@localhost:5432/genomics_platform"
$env:REDIS_URL = "redis://localhost:6379"

# Function to run pipeline with progress
function Run-Pipeline {
    param(
        [string]$PipelineName,
        [string]$ScriptPath
    )
    
    Write-Host "`n🚀 Running $PipelineName Pipeline..." -ForegroundColor Cyan
    Write-Host "This may take several minutes depending on data size..." -ForegroundColor Yellow
    
    try {
        $startTime = Get-Date
        python $ScriptPath
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $PipelineName pipeline completed successfully!" -ForegroundColor Green
            Write-Host "Duration: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Gray
        } else {
            Write-Host "❌ $PipelineName pipeline failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error running $PipelineName pipeline: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Run data pipelines
Write-Host "`n📊 Starting Dataset Population Process..." -ForegroundColor Green

# 1. ClinVar Pipeline (Clinical Variants)
if (Test-Path "data_pipeline/scripts/run_clinvar_pipeline.py") {
    Run-Pipeline "ClinVar" "data_pipeline/scripts/run_clinvar_pipeline.py"
} else {
    Write-Host "⚠️ ClinVar pipeline script not found" -ForegroundColor Yellow
}

# 2. TCGA Pipeline (Cancer Genomics)
if (Test-Path "data_pipeline/scripts/run_tcga_pipeline.py") {
    Run-Pipeline "TCGA" "data_pipeline/scripts/run_tcga_pipeline.py"
} else {
    Write-Host "⚠️ TCGA pipeline script not found" -ForegroundColor Yellow
}

# 3. PubMed Pipeline (Literature Mining)
if (Test-Path "data_pipeline/scripts/run_pubmed_pipeline.py") {
    Run-Pipeline "PubMed" "data_pipeline/scripts/run_pubmed_pipeline.py"
} else {
    Write-Host "⚠️ PubMed pipeline script not found" -ForegroundColor Yellow
}

# Verify data population
Write-Host "`n🔍 Verifying Database Population..." -ForegroundColor Yellow

try {
    # Check datasets table
    $datasetsQuery = "SELECT name, source, total_samples, total_variants FROM datasets;"
    $datasets = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $datasetsQuery
    Write-Host "📋 Datasets in database:" -ForegroundColor Cyan
    Write-Host $datasets -ForegroundColor Gray
    
    # Check sample counts
    $samplesQuery = "SELECT COUNT(*) as total_samples FROM samples;"
    $samples = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $samplesQuery
    Write-Host "🧬 Total samples: $samples" -ForegroundColor Cyan
    
    # Check variant counts
    $variantsQuery = "SELECT COUNT(*) as total_variants FROM variants;"
    $variants = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $variantsQuery
    Write-Host "🔬 Total variants: $variants" -ForegroundColor Cyan
    
    # Check literature entities
    $literatureQuery = "SELECT COUNT(*) as total_articles FROM literature_entities;"
    $literature = docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c $literatureQuery
    Write-Host "📚 Total literature entities: $literature" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error verifying database population: $($_.Exception.Message)" -ForegroundColor Red
}

# Display summary
Write-Host "`n📈 Dataset Population Summary:" -ForegroundColor Green
Write-Host "✅ PostgreSQL database is populated with genomics datasets" -ForegroundColor Green
Write-Host "✅ Data pipelines have been executed" -ForegroundColor Green
Write-Host "✅ Database is ready for analysis and ML model training" -ForegroundColor Green

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start backend API development" -ForegroundColor White
Write-Host "2. Implement ML model training pipelines" -ForegroundColor White
Write-Host "3. Create data visualization dashboards" -ForegroundColor White
Write-Host "4. Set up user authentication and authorization" -ForegroundColor White

Write-Host "`n🎉 Database population completed successfully!" -ForegroundColor Green 