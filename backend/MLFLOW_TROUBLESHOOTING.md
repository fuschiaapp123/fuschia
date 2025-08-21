# MLflow UI Troubleshooting Guide

## Issue: No tracking data visible in MLflow UI

### Root Cause
MLflow experiments were created using SQLite tracking but missing file-based metadata required by the UI.

### Solution Applied ✅

1. **Fixed Missing Experiment Metadata**:
   ```bash
   # Created missing meta.yaml files for experiments
   mlruns/1/meta.yaml  # dspy_intent_classification
   mlruns/2/meta.yaml  # dspy_prompt_optimization
   ```

2. **Verified Experiment Structure**:
   - Experiment 1: `dspy_intent_classification` - 2 runs
   - Experiment 2: `dspy_prompt_optimization` - 0 runs

### How to Start MLflow UI

**Method 1: Simple Start (Recommended)**
```bash
# From the backend directory
cd /Users/sanjay/Lab/Fuschia-alfa/backend
mlflow ui --port 5000
```

**Method 2: With Specific Backend Store**
```bash
# Explicitly specify the SQLite database
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

### Verification Steps

1. **Check Experiments**:
   ```bash
   python -c "import mlflow; [print(f'- {exp.name} (ID: {exp.experiment_id})') for exp in mlflow.search_experiments()]"
   ```

2. **Check Runs**:
   ```bash
   ls -la mlruns/1/  # Should show run directories
   ```

3. **Access UI**:
   - URL: http://localhost:5000
   - Should show both experiments
   - Runs should be visible under experiment 1

### Expected UI Content

- **Experiments Page**: Shows 2 experiments
  - `dspy_intent_classification` (active runs)
  - `dspy_prompt_optimization` (no runs yet)

- **Run Details**: For each run in experiment 1
  - Metrics: confidence_score, response_time_ms, template_match_rate
  - Parameters: model_name, message_length, etc.
  - Tags: user_role, current_module, detected_intent, etc.
  - Artifacts: prediction_result.json

### Common Issues & Fixes

**Issue**: "Malformed experiment" warnings
**Fix**: ✅ Already resolved - created missing meta.yaml files

**Issue**: Empty experiments in UI
**Fix**: Ensure you're starting MLflow UI from the backend directory

**Issue**: Port conflicts
**Fix**: MLflow UI uses port 5000, FastAPI uses 8000 - no conflicts

### Manual MLflow UI Start

```bash
# Terminal 1: FastAPI Backend (if not already running)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: MLflow UI
cd /Users/sanjay/Lab/Fuschia-alfa/backend
mlflow ui --port 5000 --host 0.0.0.0

# Access points:
# FastAPI: http://localhost:8000
# MLflow UI: http://localhost:5000
```

The tracking data should now be fully visible in the MLflow UI!