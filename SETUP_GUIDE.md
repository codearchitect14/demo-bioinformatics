# 🚀 Genomics Platform Setup Guide

## 📋 Prerequisites

- Windows 10/11
- Docker Desktop (installed)
- WSL (Windows Subsystem for Linux) - ✅ **INSTALLED**
- PowerShell (Administrator access recommended)

## ⚠️ Important: System Reboot Required

**WSL has been installed successfully, but a system reboot is required for it to work properly.**

### After Reboot:
1. **Start Docker Desktop** from the Start menu
2. **Wait for Docker to be ready** (green "Docker Desktop is running" status)
3. **Proceed with the steps below**

## 🗄️ PostgreSQL Database Setup

### Step 1: Start Genomics Platform Services

1. **Navigate to project directory**:
   ```powershell
   cd "C:\Users\Hafsa Ramzan\Boolmind\demo-bioinformatics"
   ```

2. **Start all services**:
   ```powershell
   .\start-services.ps1
   ```

   Or manually:
   ```powershell
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```powershell
   docker ps
   ```

### Step 2: Populate Database with Datasets

1. **Run the dataset population script**:
   ```powershell
   .\populate-datasets.ps1
   ```

   This will:
   - ✅ Install Python dependencies
   - ✅ Create data directories
   - ✅ Run ClinVar pipeline (clinical variants)
   - ✅ Run TCGA pipeline (cancer genomics)
   - ✅ Run PubMed pipeline (literature mining)
   - ✅ Verify data population

2. **Check database status**:
   ```powershell
   .\check-database.ps1
   ```

### Step 3: Database Connection Information

Once services are running, you can connect to:

#### PostgreSQL Database
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `genomics_platform`
- **Username**: `genomics_user`
- **Password**: `Boolmind2025@@`
- **Connection String**: `postgresql://genomics_user:Boolmind2025@@@localhost:5432/genomics_platform`

#### Redis Cache
- **Host**: `localhost`
- **Port**: `6379**
- **No authentication required**

#### MinIO Object Storage
- **API Endpoint**: `http://localhost:9000`
- **Console**: `http://localhost:9001`
- **Username**: `minioadmin`
- **Password**: `minioadmin123`

## 🔧 Database Schema

The database includes the following core tables:

### Core Tables
1. **datasets** - Dataset metadata and information
2. **samples** - Sample information and metadata
3. **variants** - Genetic variants and annotations
4. **gene_expression** - Gene expression data
5. **drug_targets** - Drug-target interactions
6. **literature_entities** - Literature mining results
7. **analysis_jobs** - Analysis job tracking
8. **model_predictions** - ML model predictions

### Indexes
- Optimized indexes for fast querying
- Composite indexes for common query patterns
- Full-text search capabilities

## 📊 Datasets to be Populated

### Phase 1 Datasets (Ready to Run)

#### 1. **ClinVar Database** 🧬
- **Source**: NCBI ClinVar
- **Data**: Clinical variants with pathogenicity annotations
- **Size**: ~1M variants
- **Use Case**: Variant interpretation, clinical significance prediction

#### 2. **TCGA (The Cancer Genome Atlas)** 🦠
- **Source**: NCI GDC Data Portal
- **Data**: Cancer genomics (gene expression, mutations, clinical)
- **Size**: ~10K samples, ~5M variants
- **Use Case**: Cancer biomarker discovery, drug response prediction

#### 3. **PubMed Literature** 📚
- **Source**: NCBI PubMed
- **Data**: Biomedical literature abstracts and entities
- **Size**: ~100K articles
- **Use Case**: Literature mining, knowledge discovery

### Phase 2 Datasets (Future)
- **1000 Genomes Project** - Population genetics
- **ENCODE** - Functional genomics
- **DrugBank/ChEMBL** - Drug-target interactions
- **GEO** - Gene expression omnibus

## 🧪 Testing the Database

### Test Connection
```powershell
# Test PostgreSQL connection
docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c "SELECT version();"
```

### View Database Schema
```powershell
# List all tables
docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c "\dt"
```

### Check Data Population
```powershell
# View dataset summary
docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c "SELECT * FROM dataset_summary;"

# Check data counts
docker exec genomics_postgres psql -U genomics_user -d genomics_platform -c "SELECT 'Samples' as table_name, COUNT(*) as count FROM samples UNION ALL SELECT 'Variants', COUNT(*) FROM variants UNION ALL SELECT 'Literature', COUNT(*) FROM literature_entities;"
```

## 📊 Environment Configuration

### Local Environment File
Copy the environment configuration:
```powershell
# Copy environment file
Copy-Item env.local .env
```

### Key Environment Variables
```bash
# Database
DATABASE_URL=postgresql://genomics_user:Boolmind2025@@@localhost:5432/genomics_platform

# Redis
REDIS_URL=redis://localhost:6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# Dataset Paths
CLINVAR_DATA_PATH=data/clinvar
TCGA_DATA_PATH=data/tcga
PUBMED_DATA_PATH=data/pubmed
```

## 🔄 Data Pipeline Integration

### Connect Data Pipelines to Database

The data pipelines are configured to connect to the local PostgreSQL database:

1. **ClinVar Pipeline**: Clinical variant data
2. **TCGA Pipeline**: Cancer genomics data
3. **PubMed Pipeline**: Literature mining data

### Run Data Pipelines
```powershell
# Run all pipelines at once
.\populate-datasets.ps1

# Or run individual pipelines
python -m data_pipeline.scripts.run_clinvar_pipeline
python -m data_pipeline.scripts.run_tcga_pipeline
python -m data_pipeline.scripts.run_pubmed_pipeline
```

## 🛠️ Troubleshooting

### Docker Issues
1. **Docker not starting**: Restart Docker Desktop after reboot
2. **Permission issues**: Run PowerShell as Administrator
3. **Port conflicts**: Check if ports 5432, 6379, 9000 are available

### Database Issues
1. **Connection refused**: Ensure Docker containers are running
2. **Authentication failed**: Verify username/password
3. **Database not found**: Check if initialization script ran

### Service Status
```powershell
# Check all services
docker ps

# Check specific service logs
docker logs genomics_postgres
docker logs genomics_redis
docker logs genomics_minio
```

## 📈 Next Steps

### 1. Backend API Development
- Set up FastAPI application
- Create database models
- Implement API endpoints
- Add authentication

### 2. Data Pipeline Integration
- Connect pipelines to database
- Implement data loading
- Add monitoring and logging

### 3. Frontend Development
- Set up React.js application
- Create data visualization components
- Implement user interface

### 4. ML Model Integration
- Set up model training pipelines
- Implement inference services
- Add model versioning

## 🔗 Useful Commands

### Database Management
```powershell
# Connect to database
docker exec -it genomics_postgres psql -U genomics_user -d genomics_platform

# Backup database
docker exec genomics_postgres pg_dump -U genomics_user genomics_platform > backup.sql

# Restore database
docker exec -i genomics_postgres psql -U genomics_user -d genomics_platform < backup.sql
```

### Service Management
```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f
```

### Data Pipeline Management
```powershell
# Install dependencies
pip install -r data_pipeline/requirements.txt

# Run all pipelines
.\populate-datasets.ps1

# Monitor pipeline status
Get-Content data_pipeline/logs/*.log -Tail 50
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review service logs
3. Verify Docker is running
4. Ensure ports are not in use
5. Check environment configuration

---

## 🎯 **IMMEDIATE NEXT STEPS**

1. **Reboot your system** (required for WSL)
2. **Start Docker Desktop** after reboot
3. **Run**: `.\start-services.ps1`
4. **Run**: `.\populate-datasets.ps1`
5. **Verify**: `.\check-database.ps1`

**Database Setup Complete!** 🎉

Your PostgreSQL database is now ready for the genomics platform. You can proceed with backend development and data pipeline integration. 