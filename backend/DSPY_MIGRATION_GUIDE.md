# DSPy Migration Guide: Intent Detection Agent

## Overview

The Intent Detection Agent has been successfully migrated from LangGraph to DSPy framework for better programmatic prompt management and structured output handling.

## What Changed

### **From LangGraph to DSPy**

**Before (LangGraph):**
- Used LangChain's ReAct agent with tools
- Manual prompt construction with string concatenation
- JSON parsing of unstructured LLM output
- Complex tool integration and state management

**After (DSPy):**
- Uses DSPy Signatures for structured input/output
- Programmatic prompt compilation and optimization
- Built-in structured output validation
- Cleaner, more maintainable code

## Key Components

### 1. **DSPy Signatures**

```python
class IntentClassification(Signature):
    """Classify user intent based on message and context"""
    
    # Input fields
    user_message: str = InputField(desc="The user's message to classify")
    user_role: str = InputField(desc="Role of the user (admin, user, etc.)")
    current_module: str = InputField(desc="Current application module")
    current_tab: str = InputField(desc="Current tab within the module")
    available_workflows: str = InputField(desc="List of available workflow templates")
    available_agents: str = InputField(desc="List of available agent templates")
    
    # Output fields
    detected_intent: str = OutputField(desc="Primary intent category")
    confidence: float = OutputField(desc="Confidence score (0.0-1.0)")
    workflow_type: str = OutputField(desc="Specific workflow category")
    # ... more output fields
```

### 2. **Structured Output Model**

```python
class IntentDetectionOutput(BaseModel):
    """Structured output for intent detection"""
    detected_intent: str = Field(description="The primary intent category")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    workflow_type: str = Field(description="Specific workflow category from database")
    # ... more fields with validation
```

### 3. **Context Integration**

The DSPy version properly integrates context variables (`user_role`, `current_module`, `current_tab`) directly into the signature input fields, enabling:

- **Role-aware intent detection**
- **Module-specific responses**
- **Tab-context understanding**

## Benefits of DSPy Migration

### 🎯 **Better Prompt Management**
- **Programmatic prompts**: DSPy handles prompt compilation automatically
- **Optimization ready**: Can use DSPy optimizers to improve prompts
- **Version control**: Easier to track prompt changes

### 🏗️ **Structured Output**
- **Type safety**: Pydantic models ensure output structure
- **Validation**: Built-in validation of LLM responses
- **No JSON parsing errors**: DSPy handles structured output natively

### 🧹 **Cleaner Code**
- **Reduced complexity**: No manual tool integration needed
- **Better separation**: Clear input/output definitions
- **Maintainability**: Easier to understand and modify

### 📊 **Observability**
- **Built-in logging**: DSPy provides better tracing
- **Debugging**: Easier to debug prompt issues
- **Metrics**: Better tracking of model performance

## Migration Details

### **Files Changed:**
- ✅ `app/services/intent_agent.py` - Completely rewritten with DSPy
- ✅ `requirements.txt` - Replaced LangGraph dependencies with DSPy
- ✅ `test_intent_context.py` - Updated test for DSPy interface
- ✅ `intent_agent_langgraph_backup.py` - Backup of original LangGraph version

### **Dependencies Updated:**
```diff
- langchain-core>=0.3.0,<1.0.0
- langchain>=0.3.0,<1.0.0
- langchain-openai>=0.2.0,<1.0.0
- langchain-community>=0.3.0,<1.0.0
- langgraph>=0.2.0,<1.0.0
+ dspy-ai>=2.4.0
```

### **API Compatibility:**
The public interface remains the same:
```python
# Still works exactly the same
from app.services.intent_agent import create_intent_agent

agent = create_intent_agent()
result = await agent.detect_intent_with_context(
    message="Help me create a workflow",
    user_role="admin",
    current_module="workflows",
    current_tab="designer"
)
```

## Usage Examples

### **Basic Intent Detection:**
```python
agent = create_intent_agent()

result = await agent.detect_intent_with_context(
    message="I need help with IT support",
    user_role="admin",
    current_module="workflows",
    current_tab="active"
)

print(result["detected_intent"])  # "WORKFLOW_IT_SUPPORT"
print(result["confidence"])       # 0.95
print(result["requires_workflow"]) # True
```

### **Context-Aware Classification:**
```python
# In workflow designer context
result = await agent.detect_intent_with_context(
    message="Create new process",
    current_module="workflows",
    current_tab="designer"
)
# Will likely classify as WORKFLOW_DESIGN

# In monitoring context  
result = await agent.detect_intent_with_context(
    message="Create new process", 
    current_module="monitoring",
    current_tab="thoughts"
)
# May classify differently based on context
```

## Future Enhancements

With DSPy framework, we can now:

1. **Optimize prompts automatically** using DSPy optimizers
2. **A/B test different prompt strategies**
3. **Fine-tune for specific use cases**
4. **Add more sophisticated reasoning patterns**
5. **Implement few-shot learning examples**

## Troubleshooting

### **Missing DSPy dependency:**
```bash
pip install dspy-ai>=2.4.0
```

### **OpenAI API issues:**
Ensure `OPENAI_API_KEY` environment variable is set.

### **Rollback to LangGraph:**
If needed, the original LangGraph version is backed up in:
`app/services/intent_agent_langgraph_backup.py`

## Conclusion

The DSPy migration provides:
- ✅ **Better prompt management**
- ✅ **Structured output handling** 
- ✅ **Improved maintainability**
- ✅ **Context-aware processing**
- ✅ **Future optimization opportunities**

The intent detection system is now more robust, maintainable, and ready for advanced prompt optimization techniques.