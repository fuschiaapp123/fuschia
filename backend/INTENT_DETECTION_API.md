# Intent Detection and Enhanced Chat System

## Overview
The enhanced chat system implements intelligent intent detection that automatically routes user messages to appropriate workflows or handlers. Every chat interaction first goes through an intent detection agent powered by LLM, which determines the user's intent and triggers the appropriate response mechanism.

## Architecture

### Intent Detection Flow
1. **User Message** → **Intent Detection Agent** → **Intent Classification**
2. **Intent Classification** → **Workflow Decision** → **Response Generation**
3. **Response Generation** → **Enhanced Chat Response** with metadata

### Intent Categories
- **SUPPORT_REQUEST**: IT issues, login problems, system access
- **HR_INQUIRY**: Payroll, benefits, time off, HR policies  
- **CUSTOMER_SERVICE**: Billing, account problems, service complaints
- **WORKFLOW_DESIGN**: Creating, modifying, understanding workflows
- **AGENT_MANAGEMENT**: AI agent configuration and capabilities
- **KNOWLEDGE_INQUIRY**: Information requests, documentation
- **SYSTEM_STATUS**: System health and operational status
- **GENERAL_CHAT**: Casual conversation, greetings

## API Endpoints

### 1. Enhanced Chat Endpoint
```
POST /api/v1/chat/enhanced
```

**Request:**
```json
{
  "messages": [{"role": "user", "content": "I can't login to my account"}],
  "model": "gpt-3.5-turbo",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "🤖 Intent Detected: Support Request\n\nI've processed your request through our IT incident management system...",
  "intent": {
    "detected_intent": "SUPPORT_REQUEST",
    "confidence": 0.95,
    "workflow_type": "IT",
    "reasoning": "User reported login issues which indicates IT support needed",
    "requires_workflow": true,
    "suggested_action": "Trigger IT support workflow"
  },
  "workflow_result": {
    "response": "I've created an incident to track your login issue...",
    "workflow_triggered": true,
    "agent_path": ["Front Desk Agent", "It Service Agent", "Incident Agent"],
    "final_agent": "Incident Agent",
    "agent_actions": [
      {
        "tool": "Create Incident",
        "status": "success",
        "result": {...}
      }
    ]
  },
  "agent_id": "intent_detection_agent",
  "agent_label": "Enhanced Chat Agent"
}
```

### 2. Intent Detection Endpoint
```
POST /api/v1/intent/detect
```

**Request:**
```json
{
  "message": "I need help with my payroll",
  "session_id": "test_session",
  "model": "gpt-3.5-turbo",
  "temperature": 0.3
}
```

**Response:**
```json
{
  "detected_intent": "HR_INQUIRY",
  "confidence": 0.92,
  "workflow_type": "HR",
  "reasoning": "User asking about payroll which is HR-related",
  "requires_workflow": true,
  "suggested_action": "Route to HR service team"
}
```

## Intent Detection Logic

### LLM-Powered Classification
The system uses GPT models to analyze user messages and classify intent with:
- **Confidence scoring** (0.0 to 1.0)
- **Contextual reasoning** for classification decisions
- **Workflow requirement determination**
- **Specific action recommendations**

### Fallback Mechanisms
- **Keyword-based classification** when LLM fails
- **Default intent assignment** for unclear messages
- **Error handling** with graceful degradation

## Workflow Integration

### Automatic Workflow Triggering
When `requires_workflow = true` and `confidence > 0.6`:
1. Load agent organization from YAML
2. Route message to appropriate service agent
3. Execute specialist agent tools
4. Generate contextual response
5. Return workflow execution results

### Workflow Types
- **IT**: Incident/Change management via ServiceNow
- **HR**: Payroll/Benefits inquiries and processing
- **Customer Service**: Billing/Account management

## Frontend Integration

### Enhanced Message Display
The chat interface automatically displays:
- **Intent detection results** with confidence scores
- **Agent routing paths** showing workflow progression  
- **Tool execution summaries** with action counts
- **Workflow-specific styling** (green for workflows)

### Metadata Structure
```typescript
interface MessageMetadata {
  intent?: {
    detected_intent: string;
    confidence: number;
    workflow_type?: string;
    reasoning: string;
    requires_workflow: boolean;
    suggested_action: string;
  };
  workflow_result?: {
    response: string;
    workflow_triggered: boolean;
    agent_path: string[];
    final_agent?: string;
    agent_actions: Array<{
      tool: string;
      status: string;
      result?: any;
      error?: string;
    }>;
  };
}
```

## Intent-Specific Handlers

### Non-Workflow Intents
- **Workflow Design**: Provides templates and guidance
- **Agent Management**: Explains agent capabilities and organization
- **Knowledge Inquiry**: Searches documentation and provides information
- **System Status**: Returns operational status dashboard
- **General Chat**: Friendly greeting and feature overview

## Testing

### Test Script
Run `python test_intent_detection.py` to test:
- Intent detection accuracy across different message types
- Enhanced chat workflow triggering
- Response format validation
- Error handling scenarios

### Example Test Cases
```python
test_cases = [
    "I can't login to my computer",           # → SUPPORT_REQUEST + IT workflow
    "When is my payroll processed?",          # → HR_INQUIRY + HR workflow  
    "Why am I charged $99 instead of $49?",  # → CUSTOMER_SERVICE + billing workflow
    "How do I create a workflow?",           # → WORKFLOW_DESIGN (no workflow)
    "Hello, how are you?",                   # → GENERAL_CHAT (no workflow)
]
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM intent detection
- `SERVICENOW_*`: Required for workflow tool execution

### Confidence Thresholds
- **Workflow Trigger**: `confidence > 0.6`
- **High Confidence**: `confidence > 0.8`
- **Fallback Mode**: `confidence < 0.5`

## Benefits

1. **Intelligent Routing**: Automatically directs users to appropriate specialists
2. **Reduced Manual Triage**: Intent detection eliminates need for manual categorization
3. **Consistent Experience**: Standardized workflow triggering across all channels
4. **Rich Context**: Detailed intent and workflow metadata for debugging and analytics
5. **Graceful Fallbacks**: System continues working even when components fail

This system transforms simple chat into an intelligent automation platform that understands user intent and takes appropriate actions automatically.