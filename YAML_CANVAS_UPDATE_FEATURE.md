# YAML Canvas Update Feature

## Overview
Enhanced YAML canvas update functionality that automatically detects and processes YAML content from workflow task responses, updating the appropriate canvas (Workflow Designer or Agent Designer) in real-time via WebSocket.

## 🔧 Backend Improvements

### Enhanced YAML Detection (`workflow_orchestrator.py` lines 221-263)
- **Improved marker detection**: Detects `YaMl_StArT` and `YaMl_EnD` markers in task responses
- **Automatic canvas type detection**: Analyzes content to determine if it's for workflow or agent canvas
- **Structured WebSocket messages**: Sends specialized canvas update messages with metadata
- **Fallback detection**: Identifies potential YAML content even without explicit markers

### Key Features:
```python
# Automatic canvas type detection
canvas_type = "workflow"  # default
if any(keyword in yaml_content.lower() for keyword in ['agent', 'role:', 'skills:', 'department:']):
    canvas_type = "agent"

# Enhanced WebSocket message format
await websocket_manager.send_execution_update(execution.id, {
    'type': 'canvas_update',
    'canvas_type': canvas_type,
    'yaml_content': yaml_content,
    'message': f"Canvas update received for {canvas_type} designer",
    'task_id': ready_tasks[i].id,
    'agent_name': ready_tasks[i].assigned_agent.name
})
```

## 🎨 Frontend Implementation

### Canvas Update Service (`canvasUpdateService.ts`)
- **Centralized processing**: Handles all canvas updates from WebSocket messages
- **YAML parsing**: Uses existing `yamlParser.ts` utilities
- **Store integration**: Updates `useAppStore` with new canvas data
- **Preview functionality**: Allows validation without applying changes

### Key Features:
- **Auto-detection**: Determines canvas type from YAML content
- **Validation**: Ensures YAML is valid before applying updates
- **Error handling**: Graceful failure with descriptive messages
- **State management**: Updates appropriate store (workflowData or agentData)

### Visual Notifications
Both WorkflowDesigner and AgentDesigner now include:
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
Workflow Task → YAML Response → Backend Detection → WebSocket Message → Frontend Processing → Canvas Update → Visual Notification
```

## 🧪 Testing

### Test Script (`test_yaml_canvas_update.py`)
- **YAML detection testing**: Verifies marker detection and canvas type identification
- **WebSocket connectivity**: Checks WebSocket service status
- **Sample data**: Includes workflow and agent YAML examples

### Test Results:
✅ Workflow YAML detection: Working  
✅ Agent YAML detection: Working  
✅ Canvas type identification: Working  
✅ WebSocket infrastructure: Ready  

## 🚀 Usage Examples

### Workflow YAML Format:
```yaml
YaMl_StArT
Nodes:
- id: 1
  name: Start Process
  type: start
  description: Initiate the workflow
- id: 2
  name: Data Validation
  type: action
  description: Validate incoming data

Edges:
- id: edge_1_2
  source: 1
  target: 2
YaMl_EnD
```

### Agent YAML Format:
```yaml
YaMl_StArT
Nodes:
- id: agent_1
  name: Data Manager
  type: coordinator
  role: coordinator
  skills: Data Management, Process Coordination
  department: Operations

Edges:
- id: edge_1_2
  source: agent_1
  target: agent_2
  description: delegates to
YaMl_EnD
```

## 📋 Technical Details

### Files Modified:
- ✅ `backend/app/services/workflow_orchestrator.py` - Enhanced YAML detection
- ✅ `frontend/src/services/canvasUpdateService.ts` - New service for canvas updates
- ✅ `frontend/src/components/layout/MainLayout.tsx` - WebSocket message handling
- ✅ `frontend/src/components/workflow/WorkflowDesigner.tsx` - Visual notifications
- ✅ `frontend/src/components/agents/AgentDesigner.tsx` - Visual notifications

### Dependencies:
- Existing `yamlParser.ts` utilities
- `useAppStore` for state management
- WebSocket service infrastructure
- ReactFlow components

## 🎯 Benefits

1. **Real-time Updates**: Canvas automatically updates when workflows return YAML
2. **Smart Detection**: Automatically determines workflow vs agent content
3. **Visual Feedback**: Clear notifications when updates occur
4. **Error Handling**: Graceful failure with user-friendly messages
5. **No Breaking Changes**: Backward compatible with existing functionality

## 🔄 Future Enhancements

1. **Undo/Redo**: Allow users to revert canvas updates
2. **Diff View**: Show what changed in the canvas update
3. **Batch Updates**: Handle multiple canvas updates in sequence
4. **User Confirmation**: Optional confirmation before applying updates
5. **Update History**: Track canvas update history for debugging

## 🐛 Troubleshooting

### Common Issues:
1. **No notifications**: Check WebSocket connection in monitoring tab
2. **Wrong canvas type**: Verify YAML content has appropriate keywords
3. **YAML not detected**: Ensure `YaMl_StArT` and `YaMl_EnD` markers are present
4. **Canvas not updating**: Check browser console for canvasUpdateService logs

### Debug Commands:
```bash
# Test YAML detection
python3 test_yaml_canvas_update.py

# Check WebSocket status
curl http://localhost:8000/api/v1/debug/debug/websocket/status
```