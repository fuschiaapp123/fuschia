# Canvas Update Feature (JSON Format)

## Overview
Enhanced canvas update functionality that automatically detects and processes JSON content from workflow task responses, updating the appropriate canvas (Workflow Designer or Agent Designer) in real-time via WebSocket.

## 🔧 Backend Implementation

### JSON Detection (`workflow_orchestrator.py`)
- **Marker detection**: Detects `JSON_START` and `JSON_END` markers in task responses
- **Automatic canvas type detection**: Analyzes content to determine if it's for workflow or agent canvas
- **Structured WebSocket messages**: Sends specialized canvas update messages with metadata
- **Fallback detection**: Identifies potential JSON content even without explicit markers

### Key Features:
```python
# Automatic canvas type detection
canvas_type = "workflow"  # default
if any(keyword in json_content.lower() for keyword in ['"role":', '"skills":', '"department":']):
    canvas_type = "agent"

# Enhanced WebSocket message format
await websocket_manager.send_execution_update(execution.id, {
    'type': 'canvas_update',
    'canvas_type': canvas_type,
    'json_content': json_content,
    'message': f"Canvas update received for {canvas_type} designer",
    'task_id': ready_tasks[i].id,
    'agent_name': ready_tasks[i].assigned_agent.name
})
```

## 🎨 Frontend Implementation

### Canvas Update Service (`canvasUpdateService.ts`)
- **Centralized processing**: Handles all canvas updates from WebSocket messages
- **JSON parsing**: Uses `canvasParser.ts` utilities with JSON.parse
- **Legacy support**: Falls back to YAML parsing for backwards compatibility
- **Store integration**: Updates `useAppStore` with new canvas data
- **Preview functionality**: Allows validation without applying changes

### Key Features:
- **Auto-detection**: Determines canvas type from content
- **Validation**: Ensures JSON is valid before applying updates
- **Error handling**: Graceful failure with descriptive messages
- **State management**: Updates appropriate store (workflowData or agentData)

### Visual Notifications
Both WorkflowDesigner and AgentDesigner include:
- **Real-time notifications**: Pop-up alerts when canvas is updated externally
- **Auto-hide**: Notifications disappear after 5 seconds
- **Manual dismiss**: Users can close notifications manually
- **Change detection**: Only shows notifications for actual content changes

## 📡 WebSocket Integration

### MainLayout WebSocket Handler
Enhanced `onExecutionUpdate` callback to:
1. **Detect canvas updates**: Check for `canvas_update` or `potential_canvas_update` types
2. **Process updates**: Use `canvasUpdateService` to apply changes
3. **Show notifications**: Display success/failure messages in chat
4. **Prevent duplicates**: Avoid duplicate message handling

### Message Flow:
```
Workflow Task → JSON Response → Backend Detection → WebSocket Message → Frontend Processing → Canvas Update → Visual Notification
```

## 🧪 Testing

### Test Script (`test_json_canvas_update.py`)
- **JSON detection testing**: Verifies marker detection and canvas type identification
- **WebSocket connectivity**: Checks WebSocket service status
- **Sample data**: Includes workflow and agent JSON examples

### Test Results:
✅ Workflow JSON detection: Working
✅ Agent JSON detection: Working
✅ Canvas type identification: Working
✅ WebSocket infrastructure: Ready

## 🚀 Usage Examples

### Workflow JSON Format:
```json
JSON_START
{
  "nodes": [
    {"id": "1", "name": "Start Process", "type": "start", "description": "Initiate the workflow"},
    {"id": "2", "name": "Data Validation", "type": "action", "description": "Validate incoming data"},
    {"id": "3", "name": "Process Data", "type": "action", "description": "Process validated data"},
    {"id": "4", "name": "End Process", "type": "end", "description": "Complete the workflow"}
  ],
  "edges": [
    {"id": "edge_1_2", "source": "1", "target": "2"},
    {"id": "edge_2_3", "source": "2", "target": "3"},
    {"id": "edge_3_4", "source": "3", "target": "4"}
  ]
}
JSON_END
```

### Agent JSON Format:
```json
JSON_START
{
  "nodes": [
    {
      "id": "agent_1",
      "name": "Data Manager",
      "type": "coordinator",
      "description": "Manages data flow and coordination",
      "role": "coordinator",
      "skills": ["Data Management", "Process Coordination"],
      "department": "Operations"
    },
    {
      "id": "agent_2",
      "name": "Validation Specialist",
      "type": "specialist",
      "description": "Specializes in data validation",
      "role": "specialist",
      "skills": ["Data Validation", "Quality Assurance"],
      "department": "Quality"
    }
  ],
  "edges": [
    {"id": "edge_agent_1_2", "source": "agent_1", "target": "agent_2", "description": "delegates validation to"}
  ]
}
JSON_END
```

## 📋 Technical Details

### Files Modified:
- ✅ `backend/app/services/workflow_orchestrator.py` - JSON detection and WebSocket messages
- ✅ `frontend/src/utils/canvasParser.ts` - JSON parsing with YAML fallback
- ✅ `frontend/src/services/canvasUpdateService.ts` - Canvas update processing
- ✅ `frontend/src/components/layout/MainLayout.tsx` - WebSocket message handling
- ✅ `frontend/src/components/workflow/WorkflowDesigner.tsx` - Visual notifications
- ✅ `frontend/src/components/agents/AgentDesigner.tsx` - Visual notifications

### Dependencies:
- `canvasParser.ts` utilities (JSON.parse with YAML fallback)
- `useAppStore` for state management
- WebSocket service infrastructure
- ReactFlow components

## 🎯 Benefits

1. **Real-time Updates**: Canvas automatically updates when workflows return JSON
2. **Smart Detection**: Automatically determines workflow vs agent content
3. **Visual Feedback**: Clear notifications when updates occur
4. **Error Handling**: Graceful failure with user-friendly messages
5. **Backward Compatible**: Still supports YAML format for legacy content
6. **Structured Data**: JSON is more reliable to parse than custom YAML

## 🔄 Future Enhancements

1. **Undo/Redo**: Allow users to revert canvas updates
2. **Diff View**: Show what changed in the canvas update
3. **Batch Updates**: Handle multiple canvas updates in sequence
4. **User Confirmation**: Optional confirmation before applying updates
5. **Update History**: Track canvas update history for debugging

## 🐛 Troubleshooting

### Common Issues:
1. **No notifications**: Check WebSocket connection in monitoring tab
2. **Wrong canvas type**: Verify JSON content has appropriate keywords (role, skills, department for agents)
3. **JSON not detected**: Ensure `JSON_START` and `JSON_END` markers are present
4. **Canvas not updating**: Check browser console for canvasUpdateService logs

### Debug Commands:
```bash
# Test JSON detection
python3 test_json_canvas_update.py

# Check WebSocket status
curl http://localhost:8000/api/v1/debug/debug/websocket/status
```

## Migration from YAML

The system now prefers JSON format but maintains backward compatibility with YAML:

| Old Format | New Format |
|------------|------------|
| `YaMl_StArT` | `JSON_START` |
| `YaMl_EnD` | `JSON_END` |
| `yaml_content` (WebSocket) | `json_content` (WebSocket) |
| Custom line-by-line parsing | `JSON.parse()` |

Both formats are supported, but JSON is recommended for new implementations.
