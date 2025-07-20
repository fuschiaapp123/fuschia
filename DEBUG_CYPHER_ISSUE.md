# Debug: Neo4j Cypher Query Issue

You're getting "API Error: Unknown error. Showing sample data." when clicking Run in the Knowledge Graph tab. Here's how to diagnose and fix this:

## Step 1: Check if Backend Server is Running

1. **Check if the FastAPI server is running:**
   ```bash
   cd /Users/sanjay/Lab/Fuschia-alfa/backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify the server is accessible:**
   - Open browser to: http://localhost:8000/docs
   - You should see the FastAPI Swagger UI with all endpoints

## Step 2: Check Browser Network Tab

1. **Open browser developer tools (F12)**
2. **Go to Network tab**
3. **Click Run button in Knowledge Graph**
4. **Look for the request to `/api/v1/knowledge/cypher`**

**Expected outcomes:**
- ✅ **200 OK**: API working correctly
- ❌ **404 Not Found**: Server not running or route not registered  
- ❌ **401 Unauthorized**: Authentication issue
- ❌ **500 Internal Server Error**: Backend error
- ❌ **CORS Error**: Cross-origin request blocked
- ❌ **No request visible**: Frontend not making the request

## Step 3: Test the API Directly

**Test with curl:**
```bash
# First get a token by logging in
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_EMAIL&password=YOUR_PASSWORD"

# Use the token to test cypher endpoint
curl -X POST "http://localhost:8000/api/v1/knowledge/cypher" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query": "MATCH (n) RETURN n LIMIT 5"}'
```

## Step 4: Check Frontend Console

**Open browser console and look for:**
- `Executing Cypher query: MATCH (n) RETURN n LIMIT 25`
- `Token: Present` (should show Present, not Missing)
- `Response status: XXX` (what status code?)
- Any error messages

## Most Likely Issues & Solutions:

### Issue 1: Backend Server Not Running
**Solution:** Start the backend server:
```bash
cd /Users/sanjay/Lab/Fuschia-alfa/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue 2: Authentication Token Missing
**Solution:** Make sure you're logged in. The error might be due to missing or expired JWT token.

### Issue 3: Neo4j Database Not Running  
**Solution:** Start Neo4j database:
```bash
cd /Users/sanjay/Lab/Fuschia-alfa
docker-compose up -d neo4j
```

### Issue 4: CORS Configuration
**Solution:** Check if CORS is configured correctly in backend settings.

### Issue 5: Route Not Registered
**Solution:** Verify the knowledge router is included in the main API router.

## Quick Fix to Test

**Add this temporary test button to the frontend:**

```typescript
// Add this in Neo4jBrowser.tsx for debugging
const testAPI = async () => {
  try {
    const response = await fetch('/api/v1/knowledge/cypher', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ query: 'MATCH (n) RETURN n LIMIT 1' })
    });
    
    console.log('Test response status:', response.status);
    console.log('Test response:', await response.text());
  } catch (error) {
    console.log('Test error:', error);
  }
};

// Add this button in the UI temporarily:
<button onClick={testAPI} className="bg-red-500 text-white p-2">Test API</button>
```

## Next Steps

1. **Check the browser console** for the debug logs I added
2. **Check the Network tab** to see the actual HTTP request/response
3. **Verify the backend server is running** at http://localhost:8000
4. **Let me know what you find** and I can provide a more specific fix

The detailed console logs I added will help us identify exactly where the issue is occurring.