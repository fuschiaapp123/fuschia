from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class DSPyEvaluationMetric(str, Enum):
    """Available evaluation metrics for DSPy"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    BLEU = "bleu"
    ROUGE = "rouge"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    CUSTOM = "custom"


class DSPyOptimizationStrategy(str, Enum):
    """Available optimization strategies for DSPy"""
    BOOTSTRAP_FEW_SHOT = "bootstrap_few_shot"
    COPRO = "copro"
    MIPRO = "mipro"
    ENSEMBLE = "ensemble"
    RANDOM_SEARCH = "random_search"
    GRID_SEARCH = "grid_search"


class DSPyExample(BaseModel):
    """A single training example for DSPy evaluation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_data: Dict[str, Any] = Field(..., description="Input fields for the example")
    expected_output: Dict[str, Any] = Field(..., description="Expected output for the example")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DSPyEvaluationConfig(BaseModel):
    """Configuration for DSPy evaluation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = Field(..., description="Workflow task ID this evaluation belongs to")
    
    # Examples and data
    examples: List[DSPyExample] = Field(default_factory=list, description="Training/evaluation examples")
    test_examples: List[DSPyExample] = Field(default_factory=list, description="Test examples for evaluation")
    
    # Evaluation settings
    metrics: List[DSPyEvaluationMetric] = Field(default_factory=list, description="Metrics to evaluate")
    custom_metric_code: Optional[str] = Field(None, description="Custom Python code for metric evaluation")
    
    # Optimization settings
    optimization_strategy: DSPyOptimizationStrategy = Field(default=DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT)
    optimization_params: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")
    
    # Evaluation parameters
    train_test_split: float = Field(default=0.8, ge=0.1, le=0.9, description="Train/test split ratio")
    cross_validation_folds: int = Field(default=5, ge=2, le=10, description="Number of CV folds")
    
    # Meta information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User ID who created this config")


class DSPyEvaluationResult(BaseModel):
    """Results from a DSPy evaluation run"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_config_id: str = Field(..., description="Config used for this evaluation")
    task_id: str = Field(..., description="Workflow task ID")
    
    # Results
    metric_scores: Dict[str, float] = Field(default_factory=dict, description="Metric name to score mapping")
    detailed_results: List[Dict[str, Any]] = Field(default_factory=list, description="Per-example results")
    
    # Optimization results
    optimized_prompt: Optional[str] = Field(None, description="Optimized prompt if optimization was run")
    optimization_history: List[Dict[str, Any]] = Field(default_factory=list, description="Optimization iterations")
    
    # Execution info
    execution_time_seconds: float = Field(..., description="Time taken for evaluation")
    model_used: str = Field(..., description="Language model used")
    dspy_version: str = Field(..., description="DSPy version used")
    
    # Status and metadata
    status: str = Field(default="completed", description="Status of evaluation")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    artifacts: Dict[str, Any] = Field(default_factory=dict, description="Additional artifacts")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DSPyOptimizationRequest(BaseModel):
    """Request to optimize a DSPy task"""
    task_id: str = Field(..., description="Workflow task ID to optimize")
    evaluation_config_id: str = Field(..., description="Evaluation config to use")
    optimization_strategy: DSPyOptimizationStrategy = Field(..., description="Optimization strategy")
    optimization_params: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    
    # Resource constraints
    max_iterations: int = Field(default=50, ge=1, le=1000, description="Maximum optimization iterations")
    timeout_minutes: int = Field(default=30, ge=1, le=300, description="Timeout in minutes")
    
    # Target metrics
    target_metric: DSPyEvaluationMetric = Field(..., description="Primary metric to optimize")
    target_score: Optional[float] = Field(None, description="Target score to achieve")
    
    # Advanced options
    use_cached_results: bool = Field(default=True, description="Use cached results when available")
    save_intermediate_results: bool = Field(default=True, description="Save intermediate optimization steps")


class DSPyTaskConfig(BaseModel):
    """Extended task configuration with DSPy evaluation settings"""
    task_id: str = Field(..., description="Workflow task ID")
    
    # Original task data
    label: str = Field(..., description="Task label")
    type: str = Field(..., description="Task type")
    description: str = Field(..., description="Task description")
    objective: Optional[str] = Field(None, description="Task objective")
    completion_criteria: Optional[str] = Field(None, description="Completion criteria")
    
    # DSPy evaluation configuration
    evaluation_enabled: bool = Field(default=False, description="Whether DSPy evaluation is enabled")
    evaluation_config: Optional[DSPyEvaluationConfig] = Field(None, description="Evaluation configuration")
    
    # Current optimization state
    current_prompt: Optional[str] = Field(None, description="Current/optimized prompt")
    last_evaluation_result: Optional[DSPyEvaluationResult] = Field(None, description="Latest evaluation result")
    optimization_history: List[str] = Field(default_factory=list, description="List of evaluation result IDs")
    
    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(..., description="User ID who last updated this")


class DSPyEvaluationSummary(BaseModel):
    """Summary of evaluation results for dashboard display"""
    task_id: str = Field(..., description="Task ID")
    task_label: str = Field(..., description="Task label for display")
    
    # Latest evaluation
    latest_evaluation_id: Optional[str] = Field(None, description="Latest evaluation result ID")
    latest_score: Optional[float] = Field(None, description="Latest primary metric score")
    latest_metric: Optional[str] = Field(None, description="Latest primary metric name")
    
    # Historical performance
    evaluation_count: int = Field(default=0, description="Total number of evaluations")
    best_score: Optional[float] = Field(None, description="Best score achieved")
    improvement_trend: Optional[str] = Field(None, description="improving/declining/stable")
    
    # Status
    optimization_status: str = Field(default="not_started", description="Optimization status")
    last_optimized_at: Optional[datetime] = Field(None, description="Last optimization timestamp")
    
    # Quick stats
    total_examples: int = Field(default=0, description="Total training examples")
    enabled_metrics: List[str] = Field(default_factory=list, description="Enabled metric names")


# Database table models (for SQLAlchemy if using SQL database)
class CreateDSPyEvaluationConfigRequest(BaseModel):
    """Request to create a new evaluation config"""
    task_id: str = Field(..., description="Workflow task ID")
    metrics: List[DSPyEvaluationMetric] = Field(default_factory=list)
    optimization_strategy: DSPyOptimizationStrategy = Field(default=DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT)
    examples: List[DSPyExample] = Field(default_factory=list)


class UpdateDSPyEvaluationConfigRequest(BaseModel):
    """Request to update an existing evaluation config"""
    examples: Optional[List[DSPyExample]] = Field(None)
    metrics: Optional[List[DSPyEvaluationMetric]] = Field(None)
    optimization_strategy: Optional[DSPyOptimizationStrategy] = Field(None)
    optimization_params: Optional[Dict[str, Any]] = Field(None)


class RunDSPyEvaluationRequest(BaseModel):
    """Request to run a DSPy evaluation"""
    evaluation_config_id: str = Field(..., description="Evaluation config to use")
    run_optimization: bool = Field(default=True, description="Whether to run optimization after evaluation")
    save_results: bool = Field(default=True, description="Whether to save results to database")