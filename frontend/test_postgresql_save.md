# 🗄️ PostgreSQL Save Functionality Test Guide

## ✨ New Save Functionality

The Process Designer Save button now saves workflows directly to **PostgreSQL database** instead of JSON files!

### 🎯 Key Features

1. **📊 Database Storage**: Workflows saved to PostgreSQL templates table
2. **👥 Team Collaboration**: Shared access across team members  
3. **🔄 Fallback Support**: Local save if database unavailable
4. **📈 Smart Analysis**: Auto-detects complexity and estimates time
5. **🏷️ Rich Metadata**: Includes tags, preview steps, and usage tracking

### 🚀 How to Test

#### Prerequisites
1. **Backend Running**: Ensure backend is running on `http://localhost:8000`
2. **Database Ready**: PostgreSQL templates table created
3. **Authentication**: User logged in (for auth tokens)

#### Step 1: Basic Save Test
1. Open **Workflow → Process Designer**
2. Create a simple workflow with 2-3 nodes
3. Edit metadata: Set name to "Test PostgreSQL Save"
4. Click **Save** button
5. Fill form:
   - Name: "My First Database Workflow"
   - Description: "Testing PostgreSQL save functionality"
   - Category: "Test"
6. Notice the green database indicator
7. Click **Save Template**
8. Should see success message with database ID

#### Step 2: Verify Database Storage
1. Use database inspection tool:
   ```bash
   curl http://localhost:8000/api/v1/db/table/templates?limit=10
   ```
2. Check for your saved workflow in the response
3. Verify all fields are populated correctly

#### Step 3: Test Complexity Detection
1. Create workflows with different sizes:
   - **Simple**: 1-3 nodes → Should detect "simple"
   - **Medium**: 6-8 nodes → Should detect "medium"  
   - **Advanced**: 12+ nodes → Should detect "advanced"
2. Save each and verify complexity is auto-detected

#### Step 4: Test Fallback Functionality
1. Stop the backend server
2. Try to save a workflow
3. Should show database connection error
4. Choose "Yes" for local fallback
5. Verify local save works as backup

#### Step 5: Test Authentication Integration
1. Save workflow while logged in
2. Check that `created_by` field is populated
3. Test permission-based access (if implemented)

### 🔍 What Gets Saved

#### Database Fields
- **name**: Workflow title
- **description**: Workflow purpose
- **category**: User-selected category
- **template_type**: "workflow" (auto-set)
- **complexity**: Auto-detected (simple/medium/advanced)
- **estimated_time**: Auto-calculated based on complexity
- **tags**: Category + "Custom" + additional tags
- **preview_steps**: First 5 node labels
- **template_data**: Complete nodes and edges JSON
- **metadata**: Creation info, node/edge counts
- **created_by**: Current user ID (if authenticated)
- **created_at**: Timestamp
- **usage_count**: Starts at 0

#### Metadata Object
```json
{
  "author": "Current User",
  "version": "1.0.0", 
  "created": "2025-01-14T10:30:00Z",
  "nodeCount": 5,
  "edgeCount": 4,
  "savedId": "uuid-here",
  "savedAt": "2025-01-14T10:30:00Z"
}
```

### 🎨 UI Improvements

#### Save Dialog Changes
- ✅ **Green Database Indicator**: Shows PostgreSQL storage
- ✅ **Clear Messaging**: "Database for team access and collaboration"
- ✅ **Backup Option**: Checkbox to also download file
- ✅ **Removed Folder Field**: No longer needed for database storage

#### Success Messages
- Shows database ID after successful save
- Includes fallback messaging for errors
- Updates workflow metadata with saved info

### 🔧 API Endpoints

#### New Workflow Endpoints
- `POST /api/v1/workflows/save` - Save workflow to database
- `GET /api/v1/workflows/` - List saved workflows
- `GET /api/v1/workflows/{id}` - Get specific workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/use` - Track usage

#### Testing API Directly
```bash
# Test save endpoint
curl -X POST http://localhost:8000/api/v1/workflows/save \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "API Test Workflow",
    "description": "Testing via API",
    "category": "Test",
    "template_data": {
      "nodes": [{"id": "1", "data": {"label": "Start"}}],
      "edges": []
    }
  }'

# List workflows
curl http://localhost:8000/api/v1/workflows/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 🐛 Troubleshooting

#### Common Issues

1. **Database Connection Failed**
   - Check backend is running
   - Verify PostgreSQL is accessible
   - Check database credentials

2. **Authentication Required**
   - Ensure user is logged in
   - Check JWT token validity
   - Verify auth headers

3. **Save Failed**
   - Check network connectivity
   - Verify API endpoint exists
   - Check browser console for errors

4. **Local Fallback Not Working**
   - Check localStorage permissions
   - Verify templateService is available
   - Check browser storage quotas

### ✅ Success Criteria

- [x] Workflows save to PostgreSQL database
- [x] Database fields populated correctly
- [x] Metadata preserved and enhanced
- [x] Complexity auto-detection works
- [x] Fallback to local storage functions
- [x] UI clearly indicates database storage
- [x] Success messages show database ID
- [x] Authentication integration works
- [x] API endpoints respond correctly
- [x] Error handling graceful

### 📊 Database Verification

Check saved workflow in database:
```sql
SELECT 
  name, 
  description, 
  category, 
  complexity, 
  template_type,
  usage_count,
  created_at,
  created_by
FROM templates 
WHERE template_type = 'workflow'
ORDER BY created_at DESC 
LIMIT 5;
```

The Process Designer now provides enterprise-grade workflow storage with PostgreSQL database integration! 🚀