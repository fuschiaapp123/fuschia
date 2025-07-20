#!/bin/bash

echo "🔧 Installing LangChain dependencies with compatible versions..."

# First, uninstall any existing LangChain packages
echo "1. Uninstalling existing LangChain packages..."
pip uninstall langchain langchain-openai langchain-core langchain-community langgraph openai pydantic-settings -y

# Install core dependencies first
echo "2. Installing core dependencies..."
pip install "pydantic>=2.5.0,<3.0.0"
pip install "pydantic-settings>=2.4.0,<3.0.0"

# Install LangChain packages in the correct order with compatible versions
echo "3. Installing langchain-core..."
pip install "langchain-core>=0.3.0,<1.0.0"

echo "4. Installing langchain-community..."
pip install "langchain-community>=0.3.0,<1.0.0"

echo "5. Installing langchain..."
pip install "langchain>=0.3.0,<1.0.0"

echo "6. Installing langchain-openai..."
pip install "langchain-openai>=0.2.0,<1.0.0"

echo "7. Installing langgraph..."
pip install "langgraph>=0.2.0,<1.0.0"

echo "8. Installing openai..."
pip install "openai>=1.0.0"

# Install remaining requirements (excluding langchain packages)
echo "9. Installing remaining requirements..."
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 neo4j==5.15.0 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6 python-dotenv==1.0.0 sqlalchemy==2.0.23 alembic==1.13.1 httpx==0.25.2 websockets==12.0 redis==5.0.1 celery==5.3.4 prometheus-client==0.19.0 structlog==23.2.0 PyYAML==6.0.1 requests==2.31.0 psycopg2-binary==2.9.9 asyncpg==0.29.0 aiosqlite==0.19.0

echo "✅ Installation complete!"
echo "Testing compatibility..."
python check_compatibility.py