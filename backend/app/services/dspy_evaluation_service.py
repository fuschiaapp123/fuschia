"""
DSPy Evaluation and Optimization Service

This service provides functionality for evaluating and optimizing DSPy tasks
within workflow templates, including:
- Example management
- Metric evaluation 
- Prompt optimization
- Result tracking
"""

from typing import List, Dict, Any, Optional, Tuple
import time
from datetime import datetime
import structlog

import dspy
from dspy.evaluate import Evaluate

from app.models.dspy_evaluation import (
    DSPyEvaluationConfig, DSPyEvaluationResult, DSPyExample,
    DSPyEvaluationMetric, DSPyOptimizationStrategy,
    DSPyOptimizationRequest, DSPyTaskConfig, DSPyEvaluationSummary,
    CreateDSPyEvaluationConfigRequest, UpdateDSPyEvaluationConfigRequest,
    RunDSPyEvaluationRequest
)

# Initialize logger
logger = structlog.get_logger()

# Try to import DSPy teleprompt modules with fallbacks
try:
    from dspy.teleprompt import BootstrapFewShot, COPRO
    # Try to import MIPRO if available, fallback if not
    try:
        from dspy.teleprompt import MIPRO
        MIPRO_AVAILABLE = True
    except ImportError:
        MIPRO_AVAILABLE = False
        print("Warning: MIPRO optimizer not available in current DSPy version")
except ImportError as e:
    print(f"Warning: Failed to import DSPy teleprompt modules: {e}")
    BootstrapFewShot = None
    COPRO = None
    MIPRO_AVAILABLE = False

class DSPyEvaluationService:
    """Service for DSPy evaluation and optimization"""
    
    def __init__(self):
        self.logger = logger.bind(service="dspy_evaluation")
        self.evaluation_configs: Dict[str, DSPyEvaluationConfig] = {}
        self.evaluation_results: Dict[str, DSPyEvaluationResult] = {}
        self.task_configs: Dict[str, DSPyTaskConfig] = {}
        
        # Cache for evaluation metrics
        self.metric_cache: Dict[str, Any] = {}
        
        # Active optimization jobs
        self.active_optimizations: Dict[str, Any] = {}
    
    async def create_evaluation_config(
        self,
        request: CreateDSPyEvaluationConfigRequest,
        created_by: str
    ) -> DSPyEvaluationConfig:
        """Create a new evaluation configuration"""
        
        config = DSPyEvaluationConfig(
            task_id=request.task_id,
            examples=request.examples,
            metrics=request.metrics,
            optimization_strategy=request.optimization_strategy,
            created_by=created_by
        )
        
        self.evaluation_configs[config.id] = config
        
        self.logger.info(
            "Created DSPy evaluation config",
            config_id=config.id,
            task_id=request.task_id,
            example_count=len(request.examples),
            metrics=request.metrics
        )
        
        return config
    
    async def update_evaluation_config(
        self,
        config_id: str,
        request: UpdateDSPyEvaluationConfigRequest
    ) -> DSPyEvaluationConfig:
        """Update an existing evaluation configuration"""
        
        if config_id not in self.evaluation_configs:
            raise ValueError(f"Evaluation config {config_id} not found")
        
        config = self.evaluation_configs[config_id]
        
        # Update fields if provided
        if request.examples is not None:
            config.examples = request.examples
        if request.metrics is not None:
            config.metrics = request.metrics
        if request.optimization_strategy is not None:
            config.optimization_strategy = request.optimization_strategy
        if request.optimization_params is not None:
            config.optimization_params = request.optimization_params
        
        config.updated_at = datetime.utcnow()
        
        self.logger.info(
            "Updated DSPy evaluation config",
            config_id=config_id,
            task_id=config.task_id
        )
        
        return config
    
    async def get_evaluation_config(self, config_id: str) -> Optional[DSPyEvaluationConfig]:
        """Get evaluation configuration by ID"""
        return self.evaluation_configs.get(config_id)
    
    async def list_evaluation_configs(self, task_id: Optional[str] = None) -> List[DSPyEvaluationConfig]:
        """List evaluation configurations, optionally filtered by task ID"""
        configs = list(self.evaluation_configs.values())
        
        if task_id:
            configs = [c for c in configs if c.task_id == task_id]
        
        return configs
    
    async def add_examples(
        self,
        config_id: str,
        examples: List[DSPyExample]
    ) -> DSPyEvaluationConfig:
        """Add examples to an evaluation configuration"""
        
        if config_id not in self.evaluation_configs:
            raise ValueError(f"Evaluation config {config_id} not found")
        
        config = self.evaluation_configs[config_id]
        config.examples.extend(examples)
        config.updated_at = datetime.utcnow()
        
        self.logger.info(
            "Added examples to evaluation config",
            config_id=config_id,
            added_count=len(examples),
            total_count=len(config.examples)
        )
        
        return config
    
    async def remove_example(
        self,
        config_id: str,
        example_id: str
    ) -> DSPyEvaluationConfig:
        """Remove an example from evaluation configuration"""
        
        if config_id not in self.evaluation_configs:
            raise ValueError(f"Evaluation config {config_id} not found")
        
        config = self.evaluation_configs[config_id]
        original_count = len(config.examples)
        config.examples = [ex for ex in config.examples if ex.id != example_id]
        
        if len(config.examples) == original_count:
            raise ValueError(f"Example {example_id} not found in config")
        
        config.updated_at = datetime.utcnow()
        
        self.logger.info(
            "Removed example from evaluation config",
            config_id=config_id,
            example_id=example_id,
            remaining_count=len(config.examples)
        )
        
        return config
    
    async def run_evaluation(
        self,
        request: RunDSPyEvaluationRequest
    ) -> DSPyEvaluationResult:
        """Run DSPy evaluation using the specified configuration"""
        
        config = await self.get_evaluation_config(request.evaluation_config_id)
        if not config:
            raise ValueError(f"Evaluation config {request.evaluation_config_id} not found")
        
        start_time = time.time()
        
        try:
            # Prepare evaluation data
            train_examples, test_examples = self._split_examples(config)
            
            # Create DSPy signature and module for the task
            task_module = await self._create_task_module(config)
            
            # Setup evaluation metrics
            evaluation_metrics = self._setup_metrics(config)
            
            # Run evaluation
            evaluator = Evaluate(
                devset=test_examples,
                metric=evaluation_metrics,
                num_threads=1,  # Keep simple for now
                display_progress=True
            )
            
            # Evaluate current performance
            baseline_score = evaluator(task_module)
            
            # Initialize results
            result = DSPyEvaluationResult(
                evaluation_config_id=request.evaluation_config_id,
                task_id=config.task_id,
                metric_scores={"baseline": baseline_score},
                model_used="gpt-3.5-turbo",  # Get from DSPy config
                dspy_version="2.4.0",  # Get from dspy.__version__
                execution_time_seconds=0  # Will be set at the end
            )
            
            # Run optimization if requested
            if request.run_optimization:
                optimized_module, optimization_history = await self._run_optimization(
                    config, task_module, train_examples, test_examples
                )
                
                # Evaluate optimized performance
                optimized_score = evaluator(optimized_module)
                
                result.metric_scores["optimized"] = optimized_score
                result.optimization_history = optimization_history
                
                # Extract optimized prompt if available
                if hasattr(optimized_module, 'signature'):
                    result.optimized_prompt = str(optimized_module.signature)
            
            # Calculate execution time
            result.execution_time_seconds = time.time() - start_time
            
            # Save results if requested
            if request.save_results:
                self.evaluation_results[result.id] = result
            
            self.logger.info(
                "DSPy evaluation completed",
                result_id=result.id,
                task_id=config.task_id,
                baseline_score=baseline_score,
                execution_time=result.execution_time_seconds
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "DSPy evaluation failed",
                config_id=request.evaluation_config_id,
                error=str(e),
                execution_time=time.time() - start_time
            )
            
            return DSPyEvaluationResult(
                evaluation_config_id=request.evaluation_config_id,
                task_id=config.task_id,
                status="failed",
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
                model_used="unknown",
                dspy_version="unknown"
            )
    
    async def optimize_task(
        self,
        request: DSPyOptimizationRequest
    ) -> DSPyEvaluationResult:
        """Run optimization for a specific task"""
        
        # Create a run evaluation request with optimization enabled
        eval_request = RunDSPyEvaluationRequest(
            evaluation_config_id=request.evaluation_config_id,
            run_optimization=True,
            save_results=True
        )
        
        # Track active optimization
        self.active_optimizations[request.task_id] = {
            "started_at": datetime.utcnow(),
            "status": "running",
            "progress": 0.0
        }
        
        try:
            result = await self.run_evaluation(eval_request)
            
            # Update optimization status
            self.active_optimizations[request.task_id]["status"] = "completed"
            self.active_optimizations[request.task_id]["progress"] = 1.0
            
            return result
            
        except Exception as e:
            self.active_optimizations[request.task_id]["status"] = "failed"
            self.active_optimizations[request.task_id]["error"] = str(e)
            raise
    
    async def get_evaluation_result(self, result_id: str) -> Optional[DSPyEvaluationResult]:
        """Get evaluation result by ID"""
        return self.evaluation_results.get(result_id)
    
    async def list_evaluation_results(
        self,
        task_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DSPyEvaluationResult]:
        """List evaluation results with optional filtering"""
        results = list(self.evaluation_results.values())
        
        if task_id:
            results = [r for r in results if r.task_id == task_id]
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        return results[offset:offset + limit]
    
    async def get_task_evaluation_summary(self, task_id: str) -> DSPyEvaluationSummary:
        """Get evaluation summary for a task"""
        
        # Get all results for this task
        task_results = [r for r in self.evaluation_results.values() if r.task_id == task_id]
        
        # Get task configuration
        task_config = self.task_configs.get(task_id)
        task_label = task_config.label if task_config else f"Task {task_id}"
        
        summary = DSPyEvaluationSummary(
            task_id=task_id,
            task_label=task_label,
            evaluation_count=len(task_results)
        )
        
        if task_results:
            # Sort by date (newest first)
            task_results.sort(key=lambda x: x.created_at, reverse=True)
            
            latest_result = task_results[0]
            summary.latest_evaluation_id = latest_result.id
            
            # Get primary metric score
            if latest_result.metric_scores:
                primary_metric = list(latest_result.metric_scores.keys())[0]
                summary.latest_score = latest_result.metric_scores[primary_metric]
                summary.latest_metric = primary_metric
            
            # Calculate best score
            all_scores = []
            for result in task_results:
                all_scores.extend(result.metric_scores.values())
            
            if all_scores:
                summary.best_score = max(all_scores)
            
            # Determine trend (simplified)
            if len(task_results) >= 3:
                recent_scores = [r.metric_scores.get('baseline', 0) for r in task_results[:3]]
                if recent_scores[0] > recent_scores[1] > recent_scores[2]:
                    summary.improvement_trend = "improving"
                elif recent_scores[0] < recent_scores[1] < recent_scores[2]:
                    summary.improvement_trend = "declining"
                else:
                    summary.improvement_trend = "stable"
        
        # Check optimization status
        if task_id in self.active_optimizations:
            summary.optimization_status = self.active_optimizations[task_id]["status"]
        
        # Get total examples from latest config
        configs = [c for c in self.evaluation_configs.values() if c.task_id == task_id]
        if configs:
            latest_config = max(configs, key=lambda x: x.updated_at)
            summary.total_examples = len(latest_config.examples)
            summary.enabled_metrics = [m.value for m in latest_config.metrics]
        
        return summary
    
    def _split_examples(
        self,
        config: DSPyEvaluationConfig
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split examples into train and test sets"""
        
        examples = config.examples
        split_point = int(len(examples) * config.train_test_split)
        
        # Convert to DSPy format
        def to_dspy_format(ex: DSPyExample) -> Dict[str, Any]:
            return {**ex.input_data, **ex.expected_output}
        
        train_examples = [to_dspy_format(ex) for ex in examples[:split_point]]
        test_examples = [to_dspy_format(ex) for ex in examples[split_point:]]
        
        return train_examples, test_examples
    
    async def _create_task_module(self, config: DSPyEvaluationConfig) -> dspy.Module:
        """Create a DSPy module for the task based on configuration"""
        
        # For now, create a simple ChainOfThought module
        # In a real implementation, this would be more sophisticated
        # based on the specific task type
        
        # Create a basic signature
        class TaskSignature(dspy.Signature):
            """Basic task signature"""
            input_text = dspy.InputField()
            output = dspy.OutputField()
        
        # Create module
        class TaskModule(dspy.Module):
            def __init__(self):
                super().__init__()
                self.predictor = dspy.ChainOfThought(TaskSignature)
            
            def forward(self, input_text):
                return self.predictor(input_text=input_text)
        
        return TaskModule()
    
    def _setup_metrics(self, config: DSPyEvaluationConfig) -> callable:
        """Setup evaluation metrics based on configuration"""
        
        def combined_metric(gold, pred, trace=None):
            """Combined evaluation metric"""
            scores = []
            
            for metric in config.metrics:
                if metric == DSPyEvaluationMetric.ACCURACY:
                    score = 1.0 if pred.output == gold.output else 0.0
                    scores.append(score)
                elif metric == DSPyEvaluationMetric.SEMANTIC_SIMILARITY:
                    # Simplified semantic similarity
                    score = len(set(pred.output.split()) & set(gold.output.split())) / \
                           len(set(pred.output.split()) | set(gold.output.split()))
                    scores.append(score)
                # Add more metrics as needed
            
            return sum(scores) / len(scores) if scores else 0.0
        
        return combined_metric
    
    async def _run_optimization(
        self,
        config: DSPyEvaluationConfig,
        task_module: dspy.Module,
        train_examples: List[Dict[str, Any]],
        test_examples: List[Dict[str, Any]]
    ) -> Tuple[dspy.Module, List[Dict[str, Any]]]:
        """Run DSPy optimization based on strategy"""
        
        optimization_history = []
        
        if config.optimization_strategy == DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT:
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config),
                max_bootstrapped_demos=4,
                max_labeled_demos=16
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.COPRO:
            optimizer = COPRO(
                metric=self._setup_metrics(config),
                breadth=10,
                depth=3
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.MIPRO:
            if MIPRO_AVAILABLE:
                optimizer = MIPRO(
                    metric=self._setup_metrics(config),
                    num_candidates=10,
                    init_temperature=1.0
                )
            else:
                # Fallback to BootstrapFewShot if MIPRO not available
                self.logger.warning("MIPRO not available, falling back to BootstrapFewShot")
                optimizer = BootstrapFewShot(
                    metric=self._setup_metrics(config)
                )
        else:
            # Default to BootstrapFewShot
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config)
            )
        
        # Compile the optimized module
        optimized_module = optimizer.compile(
            task_module,
            trainset=train_examples,
            valset=test_examples[:10]  # Use first 10 test examples for validation
        )
        
        # Record optimization history
        optimization_history.append({
            "strategy": config.optimization_strategy.value,
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": config.optimization_params
        })
        
        return optimized_module, optimization_history
    
    async def get_optimization_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current optimization status for a task"""
        return self.active_optimizations.get(task_id)


# Global service instance
dspy_evaluation_service = DSPyEvaluationService()