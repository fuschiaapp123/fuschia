# MLflow Autolog and Tracing for DSPy Intent Detection

## Overview

MLflow autolog and tracing provide automatic observability for your DSPy intent detection system without manual instrumentation. This captures detailed execution flows, LLM calls, and performance metrics automatically.

## 🚀 Features Enabled

### **1. MLflow Autolog**
- **OpenAI Autolog**: Automatically logs all OpenAI API calls made by DSPy
- **General Autolog**: Captures other ML library interactions
- **Input/Output Logging**: Records prompts and responses
- **Automatic Metrics**: Response times, token usage, costs

### **2. MLflow Tracing**
- **Execution Spans**: Detailed breakdown of intent detection pipeline
- **LLM Call Traces**: Individual DSPy model invocations
- **Chain Tracking**: End-to-end request flow visualization
- **Error Propagation**: Automatic error capture in traces

### **3. Enhanced Observability**
- **Automatic Instrumentation**: No manual logging required
- **Span Hierarchy**: Parent-child relationship tracking
- **Context Propagation**: User context flows through traces
- **Performance Insights**: Bottleneck identification

## 📊 What Gets Automatically Tracked

### **Autolog Captures:**
```
✅ OpenAI API calls (via DSPy)
✅ Prompt inputs and completions
✅ Token usage and costs
✅ Model parameters (temperature, max_tokens)
✅ Response times and latencies
✅ Error rates and failure modes
```

### **Tracing Captures:**
```
✅ Intent detection pipeline spans
✅ DSPy signature execution
✅ Template retrieval operations
✅ Context processing steps
✅ Result formatting and validation
✅ Nested function call hierarchy
```

## 🎯 Configuration Details

### **Autolog Settings:**
```python
mlflow.openai.autolog(
    log_inputs_outputs=True,  # Log prompts and responses
    log_models=False,         # Don't save model artifacts
    log_traces=True,          # Enable trace generation
    disable=False,            # Keep autolog active
    exclusive=False,          # Allow other loggers
    silent=False              # Show autolog activity
)
```

### **Tracing Decorators:**
```python
@mlflow.trace(name="dspy_intent_detection", span_type="LLM")
async def detect_intent_with_context(self, message, ...):
    # Automatic span creation for this method
    ...

@mlflow.trace(name="intent_detection_pipeline", span_type="CHAIN")
def trace_intent_detection(self, message, context):
    # Creates parent span for the entire pipeline
    ...
```

## 📈 Viewing Traces in MLflow UI

### **1. Experiments Page**
- Navigate to `dspy_intent_classification` experiment
- Click on any run to see details

### **2. Traces Tab**
- New "Traces" tab in the MLflow UI
- Shows execution tree with timing
- Expandable spans with detailed information

### **3. Trace Details**
Each trace includes:
- **Span Name**: Function or operation name
- **Duration**: Execution time
- **Input/Output**: Parameters and results
- **Metadata**: Context information
- **Tags**: User role, module, tab
- **Errors**: Exception details if any

### **4. Visual Execution Flow**
```
dspy_intent_detection (305ms)
├── intent_detection_pipeline (12ms)
│   ├── trace_context_creation (2ms)
│   └── context_validation (3ms)
├── get_workflow_templates (45ms)
│   └── database_query (38ms)
├── get_agent_templates (23ms)
│   └── database_query (18ms)
├── dspy_predict_execution (198ms)
│   ├── openai_api_call (185ms)
│   └── response_parsing (8ms)
└── result_formatting (15ms)
```

## 🔧 Usage Examples

### **Automatic Tracing (No Code Changes Needed)**
All LLM calls via DSPy are automatically traced:
```python
# This call automatically creates traces
result = await agent.detect_intent_with_context(
    message="Help me create a workflow",
    user_role="admin",
    current_module="workflows"
)
# Traces appear automatically in MLflow UI
```

### **Custom Spans (Optional)**
Add custom tracing for specific operations:
```python
@mlflow.trace(name="custom_processing", span_type="TOOL")
def process_custom_logic(data):
    # This creates a custom span
    return processed_data
```

### **Manual Trace Creation**
For fine-grained control:
```python
with mlflow.start_span(name="database_operation") as span:
    span.set_inputs({"query": query})
    result = database.execute(query)
    span.set_outputs({"rows": len(result)})
```

## 📊 Trace Analytics

### **Performance Analysis**
- **Bottleneck Identification**: Slowest spans highlighted
- **Latency Distribution**: P50, P95, P99 metrics
- **Error Rate Tracking**: Failed span percentage
- **Cost Monitoring**: Token usage and API costs

### **Pattern Detection**
- **Common Execution Paths**: Most frequent trace patterns
- **Error Correlation**: Which inputs cause failures
- **Resource Usage**: Memory and compute patterns
- **Scaling Insights**: Performance vs. load analysis

## 🎨 Viewing Options

### **1. MLflow UI Traces**
- **Timeline View**: Chronological span execution
- **Tree View**: Hierarchical span structure
- **Table View**: Tabular span data
- **Search/Filter**: Find specific traces

### **2. API Access**
```python
# Get traces programmatically
traces = mlflow.search_traces(
    experiment_ids=["1"],
    filter_string="spans.name = 'dspy_intent_detection'"
)
```

### **3. Export Options**
- **JSON Export**: Raw trace data
- **CSV Export**: Tabular span metrics
- **Visualization**: Custom dashboards

## 🔍 Debugging with Traces

### **Error Investigation**
1. **Find Failed Traces**: Filter by error status
2. **Drill Down**: Examine failed spans
3. **Input Analysis**: Review error-causing inputs
4. **Context Review**: Check user context when error occurred

### **Performance Optimization**
1. **Identify Slow Spans**: Sort by duration
2. **Analyze Patterns**: Common slow operations
3. **Compare Versions**: Before/after optimizations
4. **Resource Correlation**: Memory/CPU vs. latency

## 🚨 Important Notes

### **Privacy Considerations**
- **Input Logging**: User messages are logged (review for sensitive data)
- **Output Logging**: LLM responses are captured
- **Context Data**: User roles and modules are tracked

### **Storage Impact**
- **Trace Volume**: Each request creates multiple spans
- **Data Retention**: Configure cleanup policies
- **Database Size**: Monitor MLflow database growth

### **Performance Impact**
- **Minimal Overhead**: ~2-5ms per request
- **Async Logging**: Non-blocking trace creation
- **Configurable**: Can disable for production if needed

## 🔧 Configuration Options

### **Disable Autolog (if needed)**
```python
mlflow.openai.autolog(disable=True)
mlflow.tracing.disable()
```

### **Selective Tracing**
```python
# Only trace specific functions
@mlflow.trace(name="critical_path")
def important_function():
    ...
```

### **Environment Variables**
```bash
# Control autolog behavior
export MLFLOW_ENABLE_AUTOLOG=true
export MLFLOW_ENABLE_TRACING=true
export MLFLOW_TRACE_BUFFER_SIZE=1000
```

## 🎉 Benefits

### **Development**
- **Faster Debugging**: Visual execution flow
- **Performance Insights**: Identify optimization opportunities
- **Error Analysis**: Root cause identification
- **Code Understanding**: See actual execution paths

### **Production**
- **Real-time Monitoring**: Live performance tracking
- **Alerting**: Automated error detection
- **Capacity Planning**: Resource usage patterns
- **SLA Monitoring**: Response time tracking

Your DSPy intent detection system now has comprehensive automatic tracing and observability! 🚀