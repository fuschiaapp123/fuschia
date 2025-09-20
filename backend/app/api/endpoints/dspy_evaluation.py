"""
DSPy Evaluation and Optimization API Endpoints

This module provides REST API endpoints for DSPy evaluation and optimization
functionality, including:
- Creating and managing evaluation configurations
- Running evaluations and optimizations
- Managing examples and metrics
- Retrieving results and summaries
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from app.services.dspy_evaluation_service import dspy_evaluation_service
from app.models.dspy_evaluation import (
    DSPyEvaluationConfig, DSPyEvaluationResult, DSPyExample,
    DSPyEvaluationMetric, DSPyOptimizationStrategy,
    DSPyOptimizationRequest, DSPyEvaluationSummary,
    CreateDSPyEvaluationConfigRequest, UpdateDSPyEvaluationConfigRequest,
    RunDSPyEvaluationRequest
)
from app.auth.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dspy-evaluation", tags=["DSPy Evaluation"])


# Additional request/response models
class AddExamplesRequest(BaseModel):
    examples: List[DSPyExample]


class RemoveExampleRequest(BaseModel):
    example_id: str


class EvaluationConfigResponse(BaseModel):
    config: DSPyEvaluationConfig
    status: str = "success"
    message: str = ""


class EvaluationResultResponse(BaseModel):
    result: DSPyEvaluationResult
    status: str = "success"
    message: str = ""


# Evaluation Configuration Endpoints
@router.post("/configs", response_model=EvaluationConfigResponse)
async def create_evaluation_config(
    request: CreateDSPyEvaluationConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new DSPy evaluation configuration for a workflow task"""
    try:
        config = await dspy_evaluation_service.create_evaluation_config(
            request=request,
            created_by=current_user.id
        )
        
        return EvaluationConfigResponse(
            config=config,
            message=f"Evaluation config created for task {request.task_id}"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create evaluation config: {str(e)}"
        )


@router.get("/configs/{config_id}", response_model=EvaluationConfigResponse)
async def get_evaluation_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get evaluation configuration by ID"""
    try:
        config = await dspy_evaluation_service.get_evaluation_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Evaluation config not found")
        
        return EvaluationConfigResponse(
            config=config,
            message="Evaluation config retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get evaluation config: {str(e)}"
        )


@router.put("/configs/{config_id}", response_model=EvaluationConfigResponse)
async def update_evaluation_config(
    config_id: str,
    request: UpdateDSPyEvaluationConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Update evaluation configuration"""
    try:
        config = await dspy_evaluation_service.update_evaluation_config(
            config_id=config_id,
            request=request
        )
        
        return EvaluationConfigResponse(
            config=config,
            message="Evaluation config updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update evaluation config: {str(e)}"
        )


@router.get("/configs", response_model=List[DSPyEvaluationConfig])
async def list_evaluation_configs(
    task_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List evaluation configurations, optionally filtered by task ID"""
    try:
        configs = await dspy_evaluation_service.list_evaluation_configs(task_id=task_id)
        return configs
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list evaluation configs: {str(e)}"
        )


# Example Management Endpoints
@router.post("/configs/{config_id}/examples", response_model=EvaluationConfigResponse)
async def add_examples(
    config_id: str,
    request: AddExamplesRequest,
    current_user: User = Depends(get_current_user)
):
    """Add examples to evaluation configuration"""
    try:
        config = await dspy_evaluation_service.add_examples(
            config_id=config_id,
            examples=request.examples
        )
        
        return EvaluationConfigResponse(
            config=config,
            message=f"Added {len(request.examples)} examples to config"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add examples: {str(e)}"
        )


@router.delete("/configs/{config_id}/examples/{example_id}", response_model=EvaluationConfigResponse)
async def remove_example(
    config_id: str,
    example_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove example from evaluation configuration"""
    try:
        config = await dspy_evaluation_service.remove_example(
            config_id=config_id,
            example_id=example_id
        )
        
        return EvaluationConfigResponse(
            config=config,
            message=f"Removed example {example_id} from config"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove example: {str(e)}"
        )


# Evaluation Execution Endpoints
@router.post("/evaluate", response_model=EvaluationResultResponse)
async def run_evaluation(
    request: RunDSPyEvaluationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run DSPy evaluation (optionally with optimization)"""
    try:
        # Run evaluation in background for long-running tasks
        if request.run_optimization:
            background_tasks.add_task(
                dspy_evaluation_service.run_evaluation,
                request
            )
            
            return EvaluationResultResponse(
                result=DSPyEvaluationResult(
                    evaluation_config_id=request.evaluation_config_id,
                    task_id="",  # Will be filled when task starts
                    status="started",
                    execution_time_seconds=0,
                    model_used="",
                    dspy_version=""
                ),
                message="Evaluation started in background"
            )
        else:
            # Run synchronously for quick evaluations
            result = await dspy_evaluation_service.run_evaluation(request)
            
            return EvaluationResultResponse(
                result=result,
                message="Evaluation completed successfully"
            )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run evaluation: {str(e)}"
        )


@router.post("/optimize", response_model=EvaluationResultResponse)
async def optimize_task(
    request: DSPyOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run DSPy optimization for a task"""
    try:
        # Always run optimization in background due to long execution time
        background_tasks.add_task(
            dspy_evaluation_service.optimize_task,
            request
        )
        
        return EvaluationResultResponse(
            result=DSPyEvaluationResult(
                evaluation_config_id=request.evaluation_config_id,
                task_id=request.task_id,
                status="optimization_started",
                execution_time_seconds=0,
                model_used="",
                dspy_version=""
            ),
            message="Optimization started in background"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start optimization: {str(e)}"
        )


# Results and Status Endpoints
@router.get("/results/{result_id}", response_model=EvaluationResultResponse)
async def get_evaluation_result(
    result_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get evaluation result by ID"""
    try:
        result = await dspy_evaluation_service.get_evaluation_result(result_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Evaluation result not found")
        
        return EvaluationResultResponse(
            result=result,
            message="Evaluation result retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get evaluation result: {str(e)}"
        )


@router.get("/results", response_model=List[DSPyEvaluationResult])
async def list_evaluation_results(
    task_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """List evaluation results with optional filtering"""
    try:
        results = await dspy_evaluation_service.list_evaluation_results(
            task_id=task_id,
            limit=limit,
            offset=offset
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list evaluation results: {str(e)}"
        )


@router.get("/tasks/{task_id}/summary", response_model=DSPyEvaluationSummary)
async def get_task_evaluation_summary(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get evaluation summary for a specific task"""
    try:
        summary = await dspy_evaluation_service.get_task_evaluation_summary(task_id)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task evaluation summary: {str(e)}"
        )


@router.get("/tasks/{task_id}/optimization-status")
async def get_optimization_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get current optimization status for a task"""
    try:
        status = await dspy_evaluation_service.get_optimization_status(task_id)
        
        if not status:
            return {
                "task_id": task_id,
                "status": "not_started",
                "message": "No optimization running for this task"
            }
        
        return {
            "task_id": task_id,
            **status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get optimization status: {str(e)}"
        )


# Utility Endpoints
@router.get("/metrics", response_model=List[str])
async def list_available_metrics():
    """List available evaluation metrics"""
    return [metric.value for metric in DSPyEvaluationMetric]


@router.get("/optimization-strategies", response_model=List[str])
async def list_optimization_strategies():
    """List available optimization strategies"""
    return [strategy.value for strategy in DSPyOptimizationStrategy]


@router.post("/configs/{config_id}/validate")
async def validate_evaluation_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Validate an evaluation configuration"""
    try:
        config = await dspy_evaluation_service.get_evaluation_config(config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Evaluation config not found")
        
        # Validation logic
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check if we have examples
        if not config.examples:
            validation_results["errors"].append("No examples provided")
            validation_results["valid"] = False
        
        # Check if we have metrics
        if not config.metrics:
            validation_results["warnings"].append("No metrics specified, will use default")
        
        # Check example count for optimization
        if len(config.examples) < 10:
            validation_results["warnings"].append(
                "Less than 10 examples may lead to poor optimization results"
            )
        
        # Check train/test split
        test_count = int(len(config.examples) * (1 - config.train_test_split))
        if test_count < 3:
            validation_results["warnings"].append(
                "Very small test set may lead to unreliable evaluation"
            )
        
        return {
            "config_id": config_id,
            "validation": validation_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate evaluation config: {str(e)}"
        )