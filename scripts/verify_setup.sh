#!/bin/bash
# Setup verification script

echo "==================================="
echo "Phase 1 Setup Verification"
echo "==================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python --version 2>&1)
echo "   $python_version"
if python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "   ✅ Python 3.10+ detected"
else
    echo "   ❌ Python 3.10+ required"
    exit 1
fi
echo ""

# Check Docker
echo "2. Checking Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo "   $docker_version"
    echo "   ✅ Docker installed"
else
    echo "   ❌ Docker not found"
    exit 1
fi
echo ""

# Check if services are running
echo "3. Checking Docker services..."
if docker compose ps | grep -q "running"; then
    echo "   ✅ Docker services running"
    echo ""
    docker compose ps
else
    echo "   ⚠️  Docker services not running"
    echo "   Run: docker compose up -d"
fi
echo ""

# Check .env file
echo "4. Checking .env file..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    # Check required variables
    required_vars=("GCP_PROJECT_ID" "DOCAI_LAYOUT_PROCESSOR_ID" "DOCAI_FORM_PROCESSOR_ID" "DATABASE_URL")
    all_present=true
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            value=$(grep "^${var}=" .env | cut -d= -f2)
            if [[ $value == *"your-"* ]]; then
                echo "   ⚠️  $var needs configuration"
                all_present=false
            else
                echo "   ✅ $var configured"
            fi
        else
            echo "   ❌ $var missing"
            all_present=false
        fi
    done
    
    if [ "$all_present" = false ]; then
        echo ""
        echo "   ⚠️  Some environment variables need configuration"
    fi
else
    echo "   ❌ .env file not found"
    echo "   Run: cp .env.example .env"
    exit 1
fi
echo ""

# Check if dependencies are installed
echo "5. Checking Python dependencies..."
if python -c "import fastapi" &> /dev/null; then
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  Dependencies not installed"
    echo "   Run: pip install -r requirements.txt"
fi
echo ""

# Check GCP authentication
echo "6. Checking GCP authentication..."
if gcloud auth application-default print-access-token &> /dev/null; then
    echo "   ✅ GCP authenticated"
    project=$(gcloud config get-value project 2>/dev/null)
    echo "   Active project: $project"
else
    echo "   ⚠️  GCP not authenticated"
    echo "   Run: gcloud auth application-default login"
fi
echo ""

# Check Alembic
echo "7. Checking database migrations..."
if [ -d "alembic/versions" ]; then
    migration_count=$(ls -1 alembic/versions/*.py 2>/dev/null | grep -v __pycache__ | wc -l)
    if [ "$migration_count" -gt 0 ]; then
        echo "   ✅ Migrations exist ($migration_count files)"
    else
        echo "   ⚠️  No migrations created yet"
        echo "   Run: alembic revision --autogenerate -m 'Initial schema'"
    fi
else
    echo "   ✅ Alembic initialized"
fi
echo ""

echo "==================================="
echo "Summary"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Configure .env file with your GCP credentials"
echo "2. Start Docker services: docker compose up -d"
echo "3. Enable pgvector: docker exec -it rag_analyzer_postgres psql -U user -d rag_analyzer -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
echo "4. Generate migration: alembic revision --autogenerate -m 'Initial schema'"
echo "5. Apply migration: alembic upgrade head"
echo "6. Seed database: python scripts/seed_compliance_bodies.py"
echo "7. Start application: uvicorn app.main:app --reload"
echo ""
