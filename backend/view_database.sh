#!/bin/bash

echo "🔍 Database Inspector for Fuschia Platform"
echo "========================================"

BASE_URL="http://localhost:8000/api/v1"

# Check if backend is running
echo "📡 Checking if backend is running..."
curl -s "$BASE_URL/templates/test" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Backend is not running on http://localhost:8000"
    echo "💡 Please start the backend first: cd backend && python app.py"
    exit 1
fi
echo "✅ Backend is running"

# Function to pretty print JSON
pretty_json() {
    if command -v jq &> /dev/null; then
        echo "$1" | jq '.'
    else
        echo "$1" | python -m json.tool 2>/dev/null || echo "$1"
    fi
}

echo ""
echo "📊 Database Overview:"
echo "===================="
overview=$(curl -s "$BASE_URL/db/inspect")
pretty_json "$overview"

echo ""
echo "📋 Available Commands:"
echo "====================="
echo "1. View all tables: curl '$BASE_URL/db/inspect'"
echo "2. View users table: curl '$BASE_URL/db/table/users'"
echo "3. View templates table: curl '$BASE_URL/db/table/templates'"
echo "4. View specific table: curl '$BASE_URL/db/table/TABLE_NAME'"
echo "5. Paginate results: curl '$BASE_URL/db/table/TABLE_NAME?limit=10&offset=0'"

echo ""
echo "🔍 Quick Views:"
echo "==============="

# Show users table if it exists
echo ""
echo "👥 Users Table (first 5 rows):"
echo "------------------------------"
users_data=$(curl -s "$BASE_URL/db/table/users?limit=5")
pretty_json "$users_data"

echo ""
echo "📝 Templates Table (first 5 rows):"
echo "-----------------------------------"
templates_data=$(curl -s "$BASE_URL/db/table/templates?limit=5")
pretty_json "$templates_data"

echo ""
echo "🎉 Database inspection complete!"
echo ""
echo "💡 Tips:"
echo "  - Install 'jq' for better JSON formatting: brew install jq"
echo "  - Use the API endpoints above to explore your data"
echo "  - Check the migration guide for PostgreSQL setup"