#!/bin/bash

# Fuschia Development Environment Setup Script

set -e

echo "🚀 Setting up Fuschia Intelligent Automation Platform"
echo "=================================================="

# Check if required tools are installed
check_requirements() {
    echo "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed. Please install Node.js (version 18+) first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
        exit 1
    fi
    
    echo "✅ All requirements met"
}

# Setup environment files
setup_environment() {
    echo "Setting up environment files..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "⚠️  Please update the .env file with your actual configuration"
    else
        echo "✅ .env file already exists"
    fi
}

# Install backend dependencies
setup_backend() {
    echo "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Installed Python dependencies"
    
    cd ..
}

# Install frontend dependencies
setup_frontend() {
    echo "Setting up frontend..."
    
    cd frontend
    npm install
    echo "✅ Installed Node.js dependencies"
    cd ..
}

# Start services with Docker Compose
start_services() {
    echo "Starting services with Docker Compose..."
    
    # Start Neo4j and Redis
    docker-compose up -d neo4j redis
    
    echo "✅ Started Neo4j and Redis services"
    echo "Waiting for services to be ready..."
    sleep 10
}

# Initialize database
init_database() {
    echo "Initializing database with sample data..."
    
    cd backend
    source venv/bin/activate
    
    # Wait for Neo4j to be ready
    echo "Waiting for Neo4j to be fully ready..."
    sleep 15
    
    # Run database initialization
    python scripts/init_db.py
    
    echo "✅ Database initialized with sample data"
    cd ..
}

# Main setup function
main() {
    check_requirements
    setup_environment
    setup_backend
    setup_frontend
    start_services
    init_database
    
    echo ""
    echo "🎉 Fuschia setup completed successfully!"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with actual configuration"
    echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "3. Start the frontend: cd frontend && npm run dev"
    echo ""
    echo "Services:"
    echo "- Frontend: http://localhost:3000"
    echo "- Backend API: http://localhost:8000"
    echo "- API Documentation: http://localhost:8000/api/docs"
    echo "- Neo4j Browser: http://localhost:7474 (neo4j/password123)"
    echo ""
    echo "Sample users:"
    echo "- Admin: admin@fuschia.io / admin123"
    echo "- Manager: manager@fuschia.io / manager123"
    echo "- Analyst: analyst@fuschia.io / analyst123"
    echo "- User: user@fuschia.io / user123"
    echo ""
}

main "$@"