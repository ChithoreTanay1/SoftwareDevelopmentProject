#!/bin/bash
# Robust Database Deployment Script

set -e  # Exit on any error

echo "🚀 Starting PostgreSQL Database Deployment..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Create database and user
echo "🗃️ Creating database and user..."
psql -U postgres -c "CREATE DATABASE quiz_game;" || echo "Database might already exist"
psql -U postgres -c "CREATE USER quiz_user WITH PASSWORD 'quiz_password123';" || echo "User might already exist"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE quiz_game TO quiz_user;"
psql -U postgres -d quiz_game -c "GRANT ALL ON SCHEMA public TO quiz_user;"

# Apply performance configuration
echo "⚡ Applying performance configuration..."
psql -U postgres -d quiz_game -f database_config.sql

# Initialize database with Python
echo "🐍 Initializing database structure..."
python setup_database.py

echo "🎉 Database deployment completed successfully!"
echo ""
echo "📊 Next steps:"
echo "   1. Start your application: python run_script.py"
echo "   2. Test the API: curl http://localhost:8000/api/v1/health"
echo "   3. Check database health: curl http://localhost:8000/api/v1/stats"