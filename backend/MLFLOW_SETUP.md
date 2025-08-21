# MLflow Observability for DSPy Intent Detection

## Overview

This setup provides comprehensive observability for the DSPy intent detection system using MLflow tracking and monitoring.

## 🚀 Features

### **Automatic Tracking**
- **Request/Response Tracking**: Every intent detection call is automatically tracked
- **Performance Metrics**: Response time, confidence scores, template match rates
- **Context Awareness**: User role, current module, and tab context tracking
- **Error Monitoring**: Automatic error logging and categorization

### **Prompt Management**
- **Prompt Versioning**: Automatic versioning based on signature changes
- **Performance Comparison**: Compare different prompt versions
- **Optimization Tracking**: Track prompt optimization experiments

### **Dashboard & Analytics**
- **Real-time Overview**: Key performance indicators and trends
- **Error Analysis**: Detailed error patterns and troubleshooting
- **Model Comparison**: Performance across different model configurations
- **Trend Analysis**: Historical performance trends and patterns

## 🛠️ Setup Instructions

### 1. Install Dependencies

The MLflow dependency is already added to `requirements.txt`:
```
mlflow>=2.8.0
```

Install with:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

**⚠️ Port Configuration Note**: The FastAPI server runs on port 8000, MLflow UI runs on port 5000. No conflicts.

Set the MLflow tracking URI (optional, defaults to local SQLite):
```bash
# For local SQLite database (default - NO SERVER REQUIRED)
export MLFLOW_TRACKING_URI="sqlite:///mlflow.db"

# For remote tracking server (if you want a separate MLflow server)
export MLFLOW_TRACKING_URI="http://localhost:5000"

# For cloud storage (e.g., S3)
export MLFLOW_TRACKING_URI="s3://your-mlflow-bucket/path"
```

**Default Setup (No Port Conflicts)**:
- FastAPI Server: `http://localhost:8000`
- MLflow UI (optional): `http://localhost:5000`
- MLflow Tracking: SQLite file (no server needed)

### 3. Initialize MLflow Experiments

The experiments are automatically created on first use. To manually initialize:
```bash
curl -X POST http://localhost:8000/api/analytics/mlflow/experiments/recreate
```

## 📊 Available Endpoints

### **Analytics Dashboard**
- `GET /api/analytics/mlflow/overview?days=7` - Performance overview
- `GET /api/analytics/mlflow/trends?days=30` - Performance trends
- `GET /api/analytics/mlflow/errors?days=7` - Error analysis
- `GET /api/analytics/mlflow/model-comparison` - Model performance comparison
- `GET /api/analytics/mlflow/prompt-analysis` - Prompt version analysis
- `GET /api/analytics/mlflow/report?days=30` - Comprehensive report

### **System Health**
- `GET /api/analytics/mlflow/health` - MLflow system health check
- `POST /api/analytics/mlflow/experiments/recreate` - Recreate experiments

## 📈 Tracked Metrics

### **Core Metrics**
- `confidence_score`: Intent detection confidence (0.0-1.0)
- `response_time_ms`: Request processing time in milliseconds
- `template_match_rate`: Whether templates were successfully matched
- `available_workflow_templates`: Number of available workflow templates
- `available_agent_templates`: Number of available agent templates

### **Context Tags**
- `user_role`: User's role (admin, user, etc.)
- `current_module`: Current application module
- `current_tab`: Current tab within module
- `detected_intent`: The classified intent
- `dspy_version`: DSPy framework version
- `prompt_version`: Unique prompt signature hash

### **Parameters**
- `model_name`: LLM model used (e.g., gpt-3.5-turbo)
- `message_length`: Length of input message
- `message_word_count`: Word count of input message
- `requires_workflow`: Whether workflow execution is recommended
- `category_source`: Source of classification (database, fallback, etc.)

## 🔍 Usage Examples

### **View Performance Overview**
```bash
curl "http://localhost:8000/api/analytics/mlflow/overview?days=7"
```

Response includes:
- Total runs and success rates
- Average confidence and response time
- Intent distribution
- User role and module usage patterns

### **Analyze Performance Trends**
```bash
curl "http://localhost:8000/api/analytics/mlflow/trends?days=30"
```

Returns daily aggregated metrics for trend analysis.

### **Check System Health**
```bash
curl "http://localhost:8000/api/analytics/mlflow/health"
```

### **Generate Comprehensive Report**
```bash
curl "http://localhost:8000/api/analytics/mlflow/report?days=30"
```

## 🎯 Key Benefits

### **Observability**
- **Real-time Monitoring**: Track every intent detection request
- **Performance Insights**: Identify bottlenecks and optimization opportunities
- **Error Tracking**: Quick identification and resolution of issues

### **Optimization**
- **Prompt Engineering**: Compare prompt versions and track improvements
- **Model Selection**: Data-driven model choice based on performance
- **Context Analysis**: Understand how context affects performance

### **Compliance & Auditing**
- **Full Audit Trail**: Complete record of all predictions
- **Performance SLAs**: Track against response time and accuracy targets
- **Data Governance**: Understand usage patterns and data flows

## 🔧 Customization

### **Add Custom Metrics**
To track additional metrics, modify `app/services/mlflow_config.py`:

```python
# Add new metric constants
NEW_METRIC = "custom_metric_name"

# Log in DSPyMLflowTracker.log_prediction_result()
mlflow.log_metric(self.NEW_METRIC, custom_value)
```

### **Add Custom Tags**
```python
# Add new tag constants
NEW_TAG = "custom_tag"

# Set in DSPyMLflowTracker.start_intent_detection_run()
mlflow.set_tag(self.NEW_TAG, custom_value)
```

### **Extend Dashboard Analytics**
Add new analysis methods to `app/services/mlflow_dashboard.py` and corresponding API endpoints.

## 🚨 Troubleshooting

### **Common Issues**

1. **MLflow DB Connection Issues**
   ```bash
   # Check if MLflow server is running
   mlflow server --host 0.0.0.0 --port 5000
   ```

2. **Experiment Not Found**
   ```bash
   # Recreate experiments
   curl -X POST http://localhost:8000/api/analytics/mlflow/experiments/recreate
   ```

3. **Tracking URI Issues**
   ```bash
   # Verify tracking URI
   python -c "import mlflow; print(mlflow.get_tracking_uri())"
   ```

### **Debug Mode**
Set log level to DEBUG to see detailed MLflow operations:
```bash
export LOG_LEVEL=DEBUG
```

## 📚 MLflow UI Access

**Option 1: Local SQLite (Default - No Port Conflicts)**
```bash
# Start MLflow UI (uses local SQLite database)
mlflow ui --port 5000

# Access at http://localhost:5000
# FastAPI continues to run on http://localhost:8000
```

**Option 2: Separate MLflow Server (Advanced)**
```bash
# Terminal 1: Start MLflow tracking server
mlflow server --host 0.0.0.0 --port 5000

# Terminal 2: Set tracking URI and start FastAPI
export MLFLOW_TRACKING_URI="http://localhost:5000"
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Access MLflow UI: http://localhost:5000
# Access FastAPI: http://localhost:8000
```

The MLflow UI provides:
- Experiment comparison views
- Run details and artifacts
- Model registry management
- Metric visualization

**Port Usage Summary**:
- Port 8000: FastAPI Backend Server
- Port 5000: MLflow UI/Server (optional)
- No conflicts between services

## 🔮 Future Enhancements

- **A/B Testing Framework**: Compare different prompt strategies
- **Automated Prompt Optimization**: Integration with DSPy optimizers
- **Real-time Alerts**: Notifications for performance degradation
- **Custom Dashboards**: Business-specific analytics views
- **Model Deployment**: MLflow model serving integration