#!/bin/bash

echo "🔍 Testing Template Database API..."

# Test if backend is running
echo "📡 Testing backend connection..."
curl -s "http://localhost:8000/api/v1/templates/test" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running on http://localhost:8000"
    echo "💡 Please start the backend first: python app.py"
    exit 1
fi

# Test template database
echo "🗄️ Testing template database..."
response=$(curl -s "http://localhost:8000/api/v1/templates/test")
echo "📊 Test response: $response"

# Populate templates
echo "📝 Populating sample templates..."
populate_response=$(curl -s -X POST "http://localhost:8000/api/v1/templates/populate")
echo "✅ Populate response: $populate_response"

# Test again to see templates
echo "🔍 Testing after population..."
final_response=$(curl -s "http://localhost:8000/api/v1/templates/test")
echo "📊 Final response: $final_response"

echo "🎉 Template API test completed!"