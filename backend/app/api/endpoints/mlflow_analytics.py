"""
MLflow Analytics API endpoints for DSPy intent detection monitoring
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import structlog
from app.services.mlflow_dashboard import dashboard

logger = structlog.get_logger()
router = APIRouter(prefix="/mlflow", tags=["mlflow-analytics"])


@router.get("/overview")
async def get_experiment_overview(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get overview of intent detection performance over the last N days
    
    Returns key metrics:
    - Total runs, success rate, failure rate
    - Average confidence and response time
    - Template match rate
    - Intent distribution
    - User role and module usage patterns
    """
    try:
        overview = dashboard.get_experiment_overview(days)
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        return overview
    except Exception as e:
        logger.error("Failed to get experiment overview", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_performance_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days for trend analysis")
) -> Dict[str, Any]:
    """
    Get performance trends over time
    
    Returns daily aggregated metrics:
    - Average confidence scores with standard deviation
    - Response time trends
    - Request volume patterns
    - Template matching success rates
    """
    try:
        trends = dashboard.get_performance_trends(days)
        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])
        return trends
    except Exception as e:
        logger.error("Failed to get performance trends", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_error_analysis(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze errors")
) -> Dict[str, Any]:
    """
    Analyze errors and failure patterns
    
    Returns:
    - Error count and types
    - Recent error contexts
    - Error patterns by user role, module, etc.
    """
    try:
        errors = dashboard.get_error_analysis(days)
        if "error" in errors:
            raise HTTPException(status_code=500, detail=errors["error"])
        return errors
    except Exception as e:
        logger.error("Failed to get error analysis", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-comparison")
async def get_model_performance_comparison() -> Dict[str, Any]:
    """
    Compare performance across different model configurations
    
    Returns:
    - Performance metrics by model type
    - Confidence scores, response times
    - Run counts for statistical significance
    """
    try:
        comparison = dashboard.get_model_performance_comparison()
        if "error" in comparison:
            raise HTTPException(status_code=500, detail=comparison["error"])
        return comparison
    except Exception as e:
        logger.error("Failed to get model comparison", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompt-analysis")
async def get_prompt_version_analysis() -> Dict[str, Any]:
    """
    Analyze performance across different prompt versions
    
    Returns:
    - Performance by prompt version hash
    - Confidence and response time metrics
    - Usage frequency and recency
    - DSPy version correlation
    """
    try:
        analysis = dashboard.get_prompt_version_analysis()
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        return analysis
    except Exception as e:
        logger.error("Failed to get prompt analysis", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def export_performance_report(
    days: int = Query(30, ge=1, le=365, description="Report period in days"),
    format: str = Query("json", regex="^(json)$", description="Report format")
) -> Dict[str, Any]:
    """
    Generate comprehensive performance report
    
    Combines all analytics into a single report:
    - Overview metrics
    - Performance trends
    - Error analysis
    - Model and prompt comparisons
    """
    try:
        report = dashboard.export_performance_report(days)
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        return report
    except Exception as e:
        logger.error("Failed to generate performance report", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_mlflow_health() -> Dict[str, Any]:
    """
    Check MLflow tracking server health and configuration
    """
    try:
        import mlflow
        from app.services.mlflow_config import MLflowConfig
        
        # Check if we can access the tracking server
        client = mlflow.tracking.MlflowClient()
        experiments = client.search_experiments()
        
        # Check if our experiments exist
        intent_exp = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
        prompt_exp = mlflow.get_experiment_by_name(MLflowConfig.PROMPT_OPTIMIZATION_EXPERIMENT)
        
        health_info = {
            "status": "healthy",
            "tracking_uri": mlflow.get_tracking_uri(),
            "experiments_count": len(experiments),
            "intent_experiment_exists": intent_exp is not None,
            "prompt_experiment_exists": prompt_exp is not None,
            "intent_experiment_id": intent_exp.experiment_id if intent_exp else None,
            "prompt_experiment_id": prompt_exp.experiment_id if prompt_exp else None,
            "checked_at": logger._context.get("timestamp", "unknown")
        }
        
        return health_info
        
    except Exception as e:
        logger.error("MLflow health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": logger._context.get("timestamp", "unknown")
        }


@router.post("/experiments/recreate")
async def recreate_experiments() -> Dict[str, Any]:
    """
    Recreate MLflow experiments if they don't exist
    (Useful for initialization or recovery)
    """
    try:
        from app.services.mlflow_config import MLflowConfig
        
        MLflowConfig.setup_mlflow()
        
        return {
            "status": "success",
            "message": "Experiments recreated successfully",
            "experiments": [
                MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT,
                MLflowConfig.PROMPT_OPTIMIZATION_EXPERIMENT
            ]
        }
        
    except Exception as e:
        logger.error("Failed to recreate experiments", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))