# Multi-Agent Workflow Trigger API

## Overview
This API endpoint enables triggering multi-agent workflows based on chat input using the LangGraph pattern from trigger.ipynb. The system routes messages through a hierarchical agent organization and executes appropriate tools.

## Endpoint
```
POST /api/v1/workflow/trigger
```

## Agent Organization
The system loads agent configurations from YAML files in the `data/` directory:
- **Level 0**: Front Desk Agent (entry point)
- **Level 1**: Service Managers (IT, HR, Customer Service)  
- **Level 2**: Specialist Agents with tools (Incident, Change, Payroll, Billing, etc.)

## Request Format
```json
{
  "message": "I can't login to my account",
  "session_id": "admin_session",
  "organization_file": "agent-org-default.yaml"
}
```

## Response Format
```json
{
  "response": "I've processed your request through our IT incident management system...",
  "workflow_triggered": true,
  "agent_path": ["Front Desk Agent", "It Service Agent", "Incident Agent"],
  "final_agent": "Incident Agent",
  "agent_actions": [
    {
      "tool": "Create Incident",
      "status": "success",
      "result": {...}
    }
  ],
  "timestamp": "2025-07-11T..."
}
```

## Agent Routing Logic
The system uses keyword-based routing:

### IT Service Agent
Keywords: password, login, access, computer, system, network, software, hardware, incident, change
Tools: Get/Create Incident, Get/Create Change

### HR Service Manager  
Keywords: payroll, salary, benefits, vacation, time off, hr, human resources, overtime
Tools: Get/Create Payroll, Get/Create Benefit

### Customer Service Agent
Keywords: billing, charge, payment, invoice, order, customer, refund, account
Tools: Get/Create Billing, Get/Create Order

## ServiceNow Integration
The endpoint integrates with ServiceNow for tool execution:
- Creates incidents, changes, and other records
- Retrieves existing data
- Handles authentication and error cases

## Frontend Integration
The ChatPanel component includes a "Multi-Agent Workflow Mode" toggle that:
- Changes the UI to green theme
- Updates placeholder text for service desk scenarios
- Displays agent path and actions in response
- Shows workflow-specific indicators

## Example Usage
```bash
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need help resetting my password",
    "session_id": "user123"
  }'
```

## Test Script
Run `python test_workflow_trigger.py` to test the endpoint with sample scenarios.