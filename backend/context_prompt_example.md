# Intent Agent Context Integration

## What was changed

The `IntentDetectionAgent` in `intent_agent.py` has been updated to include `user_role`, `current_module`, and `current_tab` variables in the system prompt.

## Changes made:

1. **Modified `_create_langgraph_agent` method** to accept context parameters:
   ```python
   def _create_langgraph_agent(self, user_role=None, current_module=None, current_tab=None):
   ```

2. **Updated system prompt** to include context information when available

3. **Modified `detect_intent_with_context`** to create agent dynamically with context

## Example system prompt with context:

```
You are an intelligent intent detection agent for an enterprise automation platform.

Your role is to analyze user messages and determine their intent by:
1. Analyzing the user's context and current location in the application
2. Providing structured intent classification

CURRENT USER CONTEXT:
- User Role: admin
- Current Module: workflows
- Current Tab: designer
Use this context to better understand the user's intent and provide more relevant classifications.

CLASSIFICATION CATEGORIES:
- WORKFLOW_DESIGN - User wants to create, modify, or understand workflows
- AGENT_MANAGEMENT - Questions about AI agents, their configuration, or capabilities
[... rest of prompt ...]
```

## How it works:

1. When `detect_intent_with_context()` is called with context variables
2. A new agent is created dynamically with those context variables
3. The context is embedded directly in the system prompt
4. The agent can use this context to make better intent classifications

## Benefits:

- **Better context awareness**: Agent knows what module/tab the user is in
- **Role-based intent detection**: Can adjust responses based on user role
- **More accurate classifications**: Context helps disambiguate user intents
- **Improved user experience**: More relevant and targeted responses