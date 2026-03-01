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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dspy_evaluation import (
    DSPyEvaluationConfig, DSPyEvaluationResult, DSPyExample,
    DSPyEvaluationMetric, DSPyOptimizationStrategy,
    DSPyOptimizationRequest, DSPyTaskConfig, DSPyEvaluationSummary,
    CreateDSPyEvaluationConfigRequest, UpdateDSPyEvaluationConfigRequest,
    RunDSPyEvaluationRequest
)
from app.db.postgres import DSPyEvaluationConfigTable, DSPyEvaluationResultTable

# Initialize logger
logger = structlog.get_logger()

# Try to import DSPy teleprompt modules with fallbacks
try:
    from dspy.teleprompt import BootstrapFewShot, COPRO
    # Try to import MIPRO if available, fallback if not
    try:
        from dspy.teleprompt import MIPROv2 as MIPRO
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

        # In-memory caches (for performance)
        self.metric_cache: Dict[str, Any] = {}
        self.active_optimizations: Dict[str, Any] = {}

        # Note: Configs and results are now persisted in database
        # We no longer use in-memory dictionaries for these

    @staticmethod
    def _serialize_example(example: DSPyExample) -> Dict[str, Any]:
        """Serialize a DSPyExample to JSON-compatible dict"""
        data = example.dict()
        # Convert datetime to ISO format string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        return data

    @staticmethod
    def _deserialize_example(data: Dict[str, Any]) -> DSPyExample:
        """Deserialize a dict to DSPyExample"""
        # Convert ISO format string back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                # Parse ISO format datetime string
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If parsing fails, use current time
                data['created_at'] = datetime.utcnow()
        return DSPyExample(**data)
    
    async def create_evaluation_config(
        self,
        request: CreateDSPyEvaluationConfigRequest,
        created_by: str,
        db: AsyncSession
    ) -> DSPyEvaluationConfig:
        """Create a new evaluation configuration"""

        config = DSPyEvaluationConfig(
            task_id=request.task_id,
            examples=request.examples,
            metrics=request.metrics,
            optimization_strategy=request.optimization_strategy,
            created_by=created_by
        )

        # Save to database
        db_config = DSPyEvaluationConfigTable(
            id=config.id,
            task_id=config.task_id,
            examples=[self._serialize_example(ex) for ex in config.examples],
            metrics=[m.value for m in config.metrics],
            optimization_strategy=config.optimization_strategy.value if config.optimization_strategy else None,
            optimization_params=config.optimization_params,
            train_test_split=config.train_test_split,
            created_by=created_by
        )

        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)

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
        request: UpdateDSPyEvaluationConfigRequest,
        db: AsyncSession
    ) -> DSPyEvaluationConfig:
        """Update an existing evaluation configuration"""

        # Fetch from database
        result = await db.execute(
            select(DSPyEvaluationConfigTable).where(DSPyEvaluationConfigTable.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            raise ValueError(f"Evaluation config {config_id} not found")

        # Update fields if provided
        from sqlalchemy.orm import attributes

        if request.examples is not None:
            db_config.examples = [self._serialize_example(ex) for ex in request.examples]
            attributes.flag_modified(db_config, "examples")

        if request.metrics is not None:
            db_config.metrics = [m.value for m in request.metrics]
            attributes.flag_modified(db_config, "metrics")

        if request.optimization_strategy is not None:
            db_config.optimization_strategy = request.optimization_strategy.value

        if request.optimization_params is not None:
            db_config.optimization_params = request.optimization_params
            attributes.flag_modified(db_config, "optimization_params")

        db_config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(db_config)

        # Convert back to Pydantic model
        config = self._db_to_pydantic_config(db_config)

        self.logger.info(
            "Updated DSPy evaluation config",
            config_id=config_id,
            task_id=config.task_id
        )

        return config
    
    async def get_evaluation_config(
        self,
        config_id: str,
        db: AsyncSession
    ) -> Optional[DSPyEvaluationConfig]:
        """Get evaluation configuration by ID"""
        result = await db.execute(
            select(DSPyEvaluationConfigTable).where(DSPyEvaluationConfigTable.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            return None

        return self._db_to_pydantic_config(db_config)

    async def list_evaluation_configs(
        self,
        task_id: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[DSPyEvaluationConfig]:
        """List evaluation configurations, optionally filtered by task ID"""
        if task_id:
            result = await db.execute(
                select(DSPyEvaluationConfigTable).where(DSPyEvaluationConfigTable.task_id == task_id)
            )
        else:
            result = await db.execute(select(DSPyEvaluationConfigTable))

        db_configs = result.scalars().all()

        return [self._db_to_pydantic_config(cfg) for cfg in db_configs]
    
    async def add_examples(
        self,
        config_id: str,
        examples: List[DSPyExample],
        db: AsyncSession
    ) -> DSPyEvaluationConfig:
        """Add examples to an evaluation configuration"""

        # Fetch from database
        result = await db.execute(
            select(DSPyEvaluationConfigTable).where(DSPyEvaluationConfigTable.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            raise ValueError(f"Evaluation config {config_id} not found")

        # Add new examples
        # Create a new list to ensure SQLAlchemy detects the change
        current_examples = list(db_config.examples) if db_config.examples else []
        new_serialized_examples = [self._serialize_example(ex) for ex in examples]
        current_examples.extend(new_serialized_examples)

        # Reassign to trigger SQLAlchemy's change detection
        db_config.examples = current_examples
        db_config.updated_at = datetime.utcnow()

        # Mark the column as modified explicitly
        from sqlalchemy.orm import attributes
        attributes.flag_modified(db_config, "examples")

        await db.commit()
        await db.refresh(db_config)

        config = self._db_to_pydantic_config(db_config)

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
        example_id: str,
        db: AsyncSession
    ) -> DSPyEvaluationConfig:
        """Remove an example from evaluation configuration"""

        # Fetch from database
        result = await db.execute(
            select(DSPyEvaluationConfigTable).where(DSPyEvaluationConfigTable.id == config_id)
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            raise ValueError(f"Evaluation config {config_id} not found")

        original_count = len(db_config.examples or [])
        db_config.examples = [ex for ex in (db_config.examples or []) if ex.get('id') != example_id]

        if len(db_config.examples) == original_count:
            raise ValueError(f"Example {example_id} not found in config")

        db_config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(db_config)

        config = self._db_to_pydantic_config(db_config)

        self.logger.info(
            "Removed example from evaluation config",
            config_id=config_id,
            example_id=example_id,
            remaining_count=len(config.examples)
        )

        return config
    
    async def run_evaluation(
        self,
        request: RunDSPyEvaluationRequest,
        db: AsyncSession
    ) -> DSPyEvaluationResult:
        """Run DSPy evaluation using the specified configuration"""

        config = await self.get_evaluation_config(request.evaluation_config_id, db)
        if not config:
            raise ValueError(f"Evaluation config {request.evaluation_config_id} not found")

        # Validate that we have examples
        if not config.examples or len(config.examples) == 0:
            raise ValueError(f"No examples found in evaluation config {request.evaluation_config_id}. Please add at least one example before running evaluation.")

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
                display_progress=True,
                display_table=1
            )

            # Evaluate current performance
            baseline_result = evaluator(task_module)

            # Extract numeric score from EvaluationResult
            # The evaluator returns a numeric score directly or wrapped in an object
            if isinstance(baseline_result, (int, float)):
                baseline_score = float(baseline_result)
            elif hasattr(baseline_result, 'metric'):
                baseline_score = float(baseline_result.metric)
            else:
                # Try to convert to float
                baseline_score = float(baseline_result)

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
                self.logger.info(
                    "Optimization completed, evaluating optimized module", optimized_module=optimized_module
                )
                # Evaluate optimized performance
                optimized_result = evaluator(optimized_module)

                # Extract numeric score
                if isinstance(optimized_result, (int, float)):
                    optimized_score = float(optimized_result)
                elif hasattr(optimized_result, 'metric'):
                    optimized_score = float(optimized_result.metric)
                else:
                    optimized_score = float(optimized_result)

                result.metric_scores["optimized"] = optimized_score
                result.optimization_history = optimization_history
                
                # Extract optimized prompt if available
                if hasattr(optimized_module, 'signature'):
                    result.optimized_prompt = str(optimized_module.signature)
                self.logger.info(
                "Completed optimization for task", result=result)
            
            # Calculate execution time
            result.execution_time_seconds = time.time() - start_time

            # Save results if requested
            if request.save_results:
                await self._save_evaluation_result(result, db)

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
        request: DSPyOptimizationRequest,
        db: AsyncSession
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
            result = await self.run_evaluation(eval_request, db)

            # Update optimization status
            self.active_optimizations[request.task_id]["status"] = "completed"
            self.active_optimizations[request.task_id]["progress"] = 1.0

            return result

        except Exception as e:
            self.active_optimizations[request.task_id]["status"] = "failed"
            self.active_optimizations[request.task_id]["error"] = str(e)
            raise

    async def get_evaluation_result(
        self,
        result_id: str,
        db: AsyncSession
    ) -> Optional[DSPyEvaluationResult]:
        """Get evaluation result by ID"""
        result = await db.execute(
            select(DSPyEvaluationResultTable).where(DSPyEvaluationResultTable.id == result_id)
        )
        db_result = result.scalar_one_or_none()

        if not db_result:
            return None

        return self._db_to_pydantic_result(db_result)

    async def list_evaluation_results(
        self,
        task_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession = None
    ) -> List[DSPyEvaluationResult]:
        """List evaluation results with optional filtering"""
        if task_id:
            result = await db.execute(
                select(DSPyEvaluationResultTable)
                .where(DSPyEvaluationResultTable.task_id == task_id)
                .order_by(DSPyEvaluationResultTable.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            result = await db.execute(
                select(DSPyEvaluationResultTable)
                .order_by(DSPyEvaluationResultTable.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

        db_results = result.scalars().all()

        return [self._db_to_pydantic_result(r) for r in db_results]
    
    async def get_task_evaluation_summary(
        self,
        task_id: str,
        db: AsyncSession
    ) -> DSPyEvaluationSummary:
        """Get evaluation summary for a task"""

        # Get all results for this task from database
        task_results = await self.list_evaluation_results(task_id=task_id, limit=100, db=db)

        task_label = f"Task {task_id}"

        summary = DSPyEvaluationSummary(
            task_id=task_id,
            task_label=task_label,
            evaluation_count=len(task_results)
        )

        if task_results:
            # Already sorted by date (newest first) from list_evaluation_results
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
        configs = await self.list_evaluation_configs(task_id=task_id, db=db)
        if configs:
            latest_config = max(configs, key=lambda x: x.updated_at)
            summary.total_examples = len(latest_config.examples)
            summary.enabled_metrics = [m.value for m in latest_config.metrics]

        return summary
    
    def _split_examples(
        self,
        config: DSPyEvaluationConfig
    ) -> Tuple[List[dspy.Example], List[dspy.Example]]:
        """Split examples into train and test sets"""

        examples = config.examples

        if not examples or len(examples) == 0:
            raise ValueError("No examples available for splitting")

        # Ensure we have at least 2 examples (1 for train, 1 for test)
        if len(examples) < 2:
            raise ValueError(f"Need at least 2 examples for train/test split, but only {len(examples)} provided. Please add more examples.")

        split_point = int(len(examples) * config.train_test_split)

        # Ensure we have at least 1 example in each set
        if split_point == 0:
            split_point = 1
        elif split_point >= len(examples):
            split_point = len(examples) - 1

        # Convert to DSPy Example format
        def to_dspy_format(ex: DSPyExample) -> dspy.Example:
            # Merge input and output data
            data = {**ex.input_data, **ex.expected_output}
            return dspy.Example(**data).with_inputs(*list(ex.input_data.keys()))

        train_examples = [to_dspy_format(ex) for ex in examples[:split_point]]
        test_examples = [to_dspy_format(ex) for ex in examples[split_point:]]

        self.logger.info(
            "Split examples for evaluation",
            total=len(examples),
            train=len(train_examples),
            test=len(test_examples)
        )

        return train_examples, test_examples
    
    async def _create_task_module(self, config: DSPyEvaluationConfig) -> dspy.Module:
        """Create a DSPy module for the task based on configuration"""

        # Dynamically determine input fields from examples
        if not config.examples or len(config.examples) == 0:
            raise ValueError("Cannot create task module without examples")

        # Get input field names from the first example
        input_fields = list(config.examples[0].input_data.keys())
        output_fields = list(config.examples[0].expected_output.keys())

        # Validate that all examples have the same structure
        for ex in config.examples:
            if set(ex.input_data.keys()) != set(input_fields):
                raise ValueError(f"Inconsistent input fields across examples. Expected {input_fields}, got {list(ex.input_data.keys())}")
            if set(ex.expected_output.keys()) != set(output_fields):
                raise ValueError(f"Inconsistent output fields across examples. Expected {output_fields}, got {list(ex.expected_output.keys())}")

        # Create dynamic signature with actual field names
        signature_fields = {}
        for field_name in input_fields:
            signature_fields[field_name] = dspy.InputField()
        for field_name in output_fields:
            signature_fields[field_name] = dspy.OutputField()

        # Add docstring
        signature_fields['__doc__'] = "Dynamic task signature based on examples"

        # Create signature class dynamically
        TaskSignature = type('TaskSignature', (dspy.Signature,), signature_fields)

        # Create module
        class TaskModule(dspy.Module):
            def __init__(self, signature_cls, input_field_names):
                super().__init__()
                self.predictor = dspy.ChainOfThought(signature_cls)
                self.input_field_names = input_field_names

            def forward(self, **kwargs):
                # Only pass the expected input fields to the predictor
                input_kwargs = {k: v for k, v in kwargs.items() if k in self.input_field_names}
                return self.predictor(**input_kwargs)

        return TaskModule(TaskSignature, input_fields)
    
    def _setup_metrics(self, config: DSPyEvaluationConfig) -> callable:
        """Setup evaluation metrics based on configuration"""

        # Get output field names from the first example
        if not config.examples or len(config.examples) == 0:
            raise ValueError("Cannot setup metrics without examples")

        output_fields = list(config.examples[0].expected_output.keys())
        # Use the first output field as the primary field for evaluation
        primary_output_field = output_fields[0]

        def combined_metric(example, pred, trace=None):
            """Combined evaluation metric

            Args:
                example: dspy.Example object containing the gold standard
                pred: Prediction object from the module
                trace: Optional trace information
            """
            scores = []

            # Get the expected output from the example using the dynamic field name
            gold_output = getattr(example, primary_output_field, None)

            # Get the predicted output using the dynamic field name
            pred_output = getattr(pred, primary_output_field, None)

            if gold_output is None or pred_output is None:
                return 0.0

            for metric in config.metrics:
                if metric == DSPyEvaluationMetric.ACCURACY:
                    score = 1.0 if str(pred_output).strip() == str(gold_output).strip() else 0.0
                    scores.append(score)
                elif metric == DSPyEvaluationMetric.SEMANTIC_SIMILARITY:
                    # Simplified semantic similarity using word overlap
                    pred_words = set(str(pred_output).lower().split())
                    gold_words = set(str(gold_output).lower().split())

                    if not pred_words and not gold_words:
                        score = 1.0
                    elif not pred_words or not gold_words:
                        score = 0.0
                    else:
                        score = len(pred_words & gold_words) / len(pred_words | gold_words)
                    scores.append(score)
                # Add more metrics as needed

            return sum(scores) / len(scores) if scores else 0.0

        return combined_metric
    
    async def _run_optimization(
        self,
        config: DSPyEvaluationConfig,
        task_module: dspy.Module,
        train_examples: List[dspy.Example],
        test_examples: List[dspy.Example]
    ) -> Tuple[dspy.Module, List[Dict[str, Any]]]:
        """Run DSPy optimization based on strategy"""

        optimization_history = []

        if config.optimization_strategy == DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT:
            # BootstrapFewShot parameters - can be customized via optimization_params
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config),
                max_bootstrapped_demos=config.optimization_params.get("max_bootstrapped_demos", 4),
                max_labeled_demos=config.optimization_params.get("max_labeled_demos", 16)
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.COPRO:
            # COPRO parameters - can be customized via optimization_params
            optimizer = COPRO(
                metric=self._setup_metrics(config),
                breadth=config.optimization_params.get("breadth", 10),
                depth=config.optimization_params.get("depth", 3)
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.MIPRO:
            if MIPRO_AVAILABLE:
                # MIPRO parameters - can be customized via optimization_params
                # MIPROv2 signature: metric, auto ('light'|'medium'|'heavy'|None), num_candidates, init_temperature, etc.
                mipro_params = {
                    "metric": self._setup_metrics(config),
                    "auto": config.optimization_params.get("auto", "light"),  # Default to 'light' auto mode
                    "num_candidates": config.optimization_params.get("num_candidates", None),  # Only used if auto=None
                    "init_temperature": config.optimization_params.get("init_temperature", 1.0),
                    "max_bootstrapped_demos": config.optimization_params.get("max_bootstrapped_demos", 4),
                    "max_labeled_demos": config.optimization_params.get("max_labeled_demos", 4),
                    "verbose": config.optimization_params.get("verbose", False)
                }
                # Remove None values to use defaults
                mipro_params = {k: v for k, v in mipro_params.items() if v is not None}
                optimizer = MIPRO(**mipro_params)
            else:
                # Fallback to BootstrapFewShot if MIPRO not available
                self.logger.warning("MIPRO not available, falling back to BootstrapFewShot")
                optimizer = BootstrapFewShot(
                    metric=self._setup_metrics(config)
                )
        elif config.optimization_strategy == DSPyOptimizationStrategy.ENSEMBLE:
            # Ensemble strategy not yet implemented, fall back to BootstrapFewShot
            self.logger.warning("ENSEMBLE strategy not yet implemented, falling back to BootstrapFewShot")
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config)
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.RANDOM_SEARCH:
            # Random search strategy not yet implemented, fall back to BootstrapFewShot
            self.logger.warning("RANDOM_SEARCH strategy not yet implemented, falling back to BootstrapFewShot")
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config)
            )
        elif config.optimization_strategy == DSPyOptimizationStrategy.GRID_SEARCH:
            # Grid search strategy not yet implemented, fall back to BootstrapFewShot
            self.logger.warning("GRID_SEARCH strategy not yet implemented, falling back to BootstrapFewShot")
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config)
            )
        else:
            # Default to BootstrapFewShot for any unhandled strategy
            self.logger.warning(f"Unknown optimization strategy {config.optimization_strategy}, falling back to BootstrapFewShot")
            optimizer = BootstrapFewShot(
                metric=self._setup_metrics(config)
            )

        # Compile the optimized module
        # BootstrapFewShot only accepts 'trainset', not 'valset'
        optimized_module = optimizer.compile(
            task_module,
            trainset=train_examples
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

    # Helper methods for database conversions

    def _db_to_pydantic_config(self, db_config: DSPyEvaluationConfigTable) -> DSPyEvaluationConfig:
        """Convert database config model to Pydantic model"""
        # Convert examples from dict to DSPyExample objects
        examples = [self._deserialize_example(ex) for ex in (db_config.examples or [])]

        # Convert metrics from strings to enum
        metrics = [DSPyEvaluationMetric(m) for m in (db_config.metrics or [])]

        # Convert optimization strategy from string to enum
        optimization_strategy = None
        if db_config.optimization_strategy:
            optimization_strategy = DSPyOptimizationStrategy(db_config.optimization_strategy)

        return DSPyEvaluationConfig(
            id=db_config.id,
            task_id=db_config.task_id,
            examples=examples,
            metrics=metrics,
            optimization_strategy=optimization_strategy,
            optimization_params=db_config.optimization_params or {},
            train_test_split=db_config.train_test_split if isinstance(db_config.train_test_split, float) else 0.8,
            created_by=db_config.created_by,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at
        )

    def _db_to_pydantic_result(self, db_result: DSPyEvaluationResultTable) -> DSPyEvaluationResult:
        """Convert database result model to Pydantic model"""
        # Handle execution_time_seconds which may be stored as JSON
        execution_time = db_result.execution_time_seconds
        if not isinstance(execution_time, (int, float)):
            execution_time = float(execution_time) if execution_time else 0.0

        return DSPyEvaluationResult(
            id=db_result.id,
            evaluation_config_id=db_result.evaluation_config_id,
            task_id=db_result.task_id,
            status=db_result.status,
            metric_scores=db_result.metric_scores or {},
            optimized_prompt=db_result.optimized_prompt,
            optimization_history=db_result.optimization_history or [],
            model_used=db_result.model_used,
            dspy_version=db_result.dspy_version,
            execution_time_seconds=execution_time,
            error_message=db_result.error_message,
            created_at=db_result.created_at
        )

    async def _save_evaluation_result(
        self,
        result: DSPyEvaluationResult,
        db: AsyncSession
    ) -> None:
        """Save evaluation result to database"""
        db_result = DSPyEvaluationResultTable(
            id=result.id,
            evaluation_config_id=result.evaluation_config_id,
            task_id=result.task_id,
            status=result.status,
            metric_scores=result.metric_scores,
            optimized_prompt=result.optimized_prompt,
            optimization_history=result.optimization_history,
            model_used=result.model_used,
            dspy_version=result.dspy_version,
            execution_time_seconds=result.execution_time_seconds,
            error_message=result.error_message
        )

        db.add(db_result)
        await db.commit()
        await db.refresh(db_result)


# Global service instance
dspy_evaluation_service = DSPyEvaluationService()