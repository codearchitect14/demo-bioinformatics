# 🧬 Genomics Platform FastAPI Backend

A production-ready FastAPI backend for the AI-powered genomics platform, providing REST API endpoints for variant analysis, drug discovery, and genomics data access.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database (running on localhost:5432)
- Docker (optional, for containerized deployment)

### Installation

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
   ```

2. **Start the server:**
   ```bash
   # Option 1: Using the startup script
   python start_server.py
   
   # Option 2: Using uvicorn directly
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Access the API:**
   - API Base URL: http://127.0.0.1:8000
   - Interactive Documentation: http://127.0.0.1:8000/docs
   - Alternative Documentation: http://127.0.0.1:8000/redoc

## 📊 API Endpoints

### Health & Status
- `GET /` - Root endpoint with API information
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check with database status
- `GET /api/v1/health/ready` - Readiness check for container orchestration
- `GET /api/v1/health/live` - Liveness check for container orchestration

### Datasets
- `GET /api/v1/datasets` - List all datasets with pagination
- `GET /api/v1/datasets/{dataset_id}` - Get specific dataset
- `GET /api/v1/datasets/{dataset_id}/stats` - Get dataset statistics
- `GET /api/v1/datasets/sources` - Get all data sources

### Variants
- `GET /api/v1/variants` - List variants with filtering and pagination
- `GET /api/v1/variants/{variant_id}` - Get specific variant
- `GET /api/v1/variants/search` - Search variants by genomic coordinates
- `GET /api/v1/variants/stats` - Get variant statistics

### Samples
- `GET /api/v1/samples` - List samples with filtering and pagination
- `GET /api/v1/samples/{sample_id}` - Get specific sample

### Drugs
- `GET /api/v1/drugs` - List drug-target interactions
- `GET /api/v1/drugs/{drug_id}` - Get specific drug

## 🗄️ Database Schema

The backend uses PostgreSQL with the following core tables:

### Core Tables
- **datasets** - Genomics datasets (TCGA, ClinVar, PubMed, etc.)
- **variants** - Genomic variants with annotations
- **samples** - Biological samples with metadata
- **gene_expression** - Transcriptomics data
- **literature_entities** - Extracted biomedical entities
- **drug_targets** - Drug-target interactions
- **analysis_jobs** - Computational analysis workflows
- **model_predictions** - ML model outputs

### Key Features
- **Connection Pooling** - Efficient database connection management
- **Pagination** - All list endpoints support pagination
- **Filtering** - Advanced filtering capabilities
- **Error Handling** - Comprehensive error handling and logging
- **CORS Support** - Cross-origin resource sharing enabled
- **OpenAPI Documentation** - Auto-generated API documentation

## 🔧 Configuration

### Database Connection
The database connection is configured in `app/database.py`:
```python
DATABASE_URL = "postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform"
```

### Environment Variables
For production, consider using environment variables:
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
export API_HOST="0.0.0.0"
export API_PORT="8000"
```

## 🧪 Testing

Run the API test script:
```bash
python test_api.py
```

This will test all major endpoints and display the results.

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration and connection
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── variant.py
│   │   ├── sample.py
│   │   ├── gene_expression.py
│   │   ├── literature_entity.py
│   │   ├── drug_target.py
│   │   ├── analysis_job.py
│   │   └── model_prediction.py
│   ├── api/                 # API endpoints
│   │   └── v1/
│   │       ├── health.py
│   │       ├── datasets.py
│   │       ├── variants.py
│   │       ├── samples.py
│   │       └── drugs.py
│   ├── schemas/             # Pydantic schemas (future)
│   ├── services/            # Business logic (future)
│   ├── ml/                  # ML models (future)
│   └── utils/               # Utility functions (future)
├── tests/                   # Test files
├── start_server.py          # Server startup script
├── test_api.py              # API testing script
└── README.md                # This file
```

## 🚀 Production Deployment

### Using Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔒 Security Considerations

- **CORS Configuration** - Currently allows all origins (configure for production)
- **Database Security** - Use environment variables for credentials
- **Input Validation** - All inputs are validated using Pydantic
- **Error Handling** - Sensitive information is not exposed in error messages

## 📈 Performance Features

- **Connection Pooling** - SQLAlchemy connection pool with 10-20 connections
- **Pagination** - Efficient pagination for large datasets
- **Indexing** - Database indexes on frequently queried columns
- **Caching** - Ready for Redis integration (future enhancement)

## 🔮 Future Enhancements

- **Authentication & Authorization** - JWT-based authentication
- **Rate Limiting** - API rate limiting
- **Caching** - Redis integration for caching
- **ML Model Integration** - Direct ML model inference endpoints
- **File Upload** - VCF, BAM file upload and processing
- **Real-time Updates** - WebSocket support for real-time data
- **Advanced Analytics** - Statistical analysis endpoints

## 📞 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs for error details
3. Test database connectivity
4. Verify all dependencies are installed

---

**🎉 Your Genomics Platform API is now ready to serve data!** 