"""
MLflow configuration and utilities for DSPy intent detection observability
"""

import os
import mlflow
import mlflow.tracking
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime, timezone
import json
import hashlib

logger = structlog.get_logger()


class MLflowConfig:
    """MLflow configuration and setup for DSPy intent detection"""
    
    # Experiment names
    INTENT_CLASSIFICATION_EXPERIMENT = "dspy_intent_classification"
    PROMPT_OPTIMIZATION_EXPERIMENT = "dspy_prompt_optimization"
    
    # Metric names
    CONFIDENCE_METRIC = "confidence_score"
    ACCURACY_METRIC = "accuracy"
    RESPONSE_TIME_METRIC = "response_time_ms"
    TEMPLATE_MATCH_RATE = "template_match_rate"
    
    # Tag names
    USER_ROLE_TAG = "user_role"
    MODULE_TAG = "current_module"
    TAB_TAG = "current_tab"
    INTENT_TAG = "detected_intent"
    DSP_VERSION_TAG = "dspy_version"
    PROMPT_VERSION_TAG = "prompt_version"
    
    @classmethod
    def setup_mlflow(cls) -> None:
        """Initialize MLflow configuration"""
        try:
            # Set MLflow tracking URI (can be overridden by environment variable)
            tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
            
            # Validate tracking URI to prevent port conflicts
            if "localhost:8000" in tracking_uri or ":8000" in tracking_uri:
                logger.warning(
                    "MLflow tracking URI uses port 8000 (conflicts with FastAPI). "
                    "Consider using port 5000 for MLflow server."
                )
            
            mlflow.set_tracking_uri(tracking_uri)
            
            # Create experiments if they don't exist
            cls._ensure_experiment_exists(cls.INTENT_CLASSIFICATION_EXPERIMENT)
            cls._ensure_experiment_exists(cls.PROMPT_OPTIMIZATION_EXPERIMENT)
            
            # Set default experiment for autolog traces
            mlflow.set_experiment(cls.INTENT_CLASSIFICATION_EXPERIMENT)
            
            # Enable MLflow autolog with tracing after setting experiment
            cls._enable_autolog_and_tracing()
            
            logger.info("MLflow configured successfully with autolog and tracing", tracking_uri=tracking_uri)
            
        except Exception as e:
            logger.error("Failed to setup MLflow", error=str(e))
            logger.info(
                "MLflow setup failed - tracking will be disabled. "
                "This won't affect the core functionality."
            )
    
    @classmethod
    def _enable_autolog_and_tracing(cls) -> None:
        """Enable MLflow autolog and tracing for comprehensive observability"""
        try:
            import mlflow.tracing
            
            # Enable tracing first
            mlflow.tracing.enable()
            
            # Enable OpenAI autolog for DSPy/LLM calls with experiment context
            try:
                # Ensure we're in the right experiment for autolog traces
                current_experiment = mlflow.get_experiment_by_name(cls.INTENT_CLASSIFICATION_EXPERIMENT)
                if current_experiment:
                    mlflow.set_experiment(cls.INTENT_CLASSIFICATION_EXPERIMENT)
                
                mlflow.openai.autolog(
                    disable=False,
                    exclusive=False,
                    disable_for_unsupported_versions=False,
                    silent=False,
                    log_traces=True
                )
                logger.info("OpenAI autolog enabled for experiment", experiment=cls.INTENT_CLASSIFICATION_EXPERIMENT)
            except Exception as e:
                logger.warning("OpenAI autolog not available", error=str(e))
            
            # Enable general autolog for other ML libraries  
            try:
                mlflow.autolog(
                    log_input_examples=True,
                    log_model_signatures=True,
                    log_models=False,  # Don't log models to save space
                    log_datasets=False,
                    log_traces=True,  # Add tracing to general autolog too
                    disable=False,
                    exclusive=False,
                    silent=False
                )
                logger.info("General autolog enabled")
            except Exception as e:
                logger.warning("General autolog failed", error=str(e))
            
            logger.info("MLflow autolog and tracing configuration completed")
            
        except Exception as e:
            logger.warning("Failed to enable MLflow autolog/tracing", error=str(e))
            logger.info("Continuing without autolog - manual tracking will still work")
    
    @classmethod
    def _ensure_experiment_exists(cls, experiment_name: str) -> str:
        """Ensure experiment exists and return experiment ID"""
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
                logger.info("Created MLflow experiment", name=experiment_name, id=experiment_id)
                return experiment_id
            else:
                return experiment.experiment_id
        except Exception as e:
            logger.error("Failed to create experiment", name=experiment_name, error=str(e))
            return "0"  # Default experiment


class DSPyMLflowTracker:
    """MLflow tracking wrapper for DSPy intent detection with autolog and tracing"""
    
    def __init__(self):
        self.logger = logger.bind(component="DSPyMLflowTracker")
        MLflowConfig.setup_mlflow()
    
    @mlflow.trace(name="intent_detection_pipeline", span_type="CHAIN")
    def trace_intent_detection(self, message: str, context: dict) -> dict:
        """Traced version of intent detection for automatic span tracking"""
        # This will be called by the main detection method
        # MLflow will automatically create traces and spans
        return {
            "message": message,
            "context": context,
            "traced": True
        }
    
    def create_prompt_signature(self, signature_inputs: Dict[str, Any]) -> str:
        """Create a unique signature for the prompt based on inputs"""
        # Create a hash of the signature structure for versioning
        signature_str = json.dumps(signature_inputs, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:8]
    
    def start_intent_detection_run(
        self,
        user_message: str,
        user_role: Optional[str] = None,
        current_module: Optional[str] = None,
        current_tab: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo"
    ) -> mlflow.ActiveRun:
        """Start an MLflow run for intent detection"""
        try:
            mlflow.set_experiment(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            
            run = mlflow.start_run()
            
            # Log parameters
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("message_length", len(user_message))
            mlflow.log_param("message_word_count", len(user_message.split()))
            
            # Log context as tags
            if user_role:
                mlflow.set_tag(MLflowConfig.USER_ROLE_TAG, user_role)
            if current_module:
                mlflow.set_tag(MLflowConfig.MODULE_TAG, current_module)
            if current_tab:
                mlflow.set_tag(MLflowConfig.TAB_TAG, current_tab)
            
            # Log system info
            mlflow.set_tag(MLflowConfig.DSP_VERSION_TAG, self._get_dspy_version())
            mlflow.set_tag("timestamp", datetime.now(timezone.utc).isoformat())
            
            # Log input (truncated for storage)
            input_preview = user_message[:200] + "..." if len(user_message) > 200 else user_message
            mlflow.log_param("user_message_preview", input_preview)
            
            self.logger.info("Started MLflow run for intent detection", run_id=run.info.run_id)
            return run
            
        except Exception as e:
            self.logger.error("Failed to start MLflow run", error=str(e))
            # Return a mock run that won't cause errors
            return None
    
    def log_prediction_result(
        self,
        result: Dict[str, Any],
        response_time_ms: float,
        signature_inputs: Dict[str, Any],
        available_templates: Dict[str, List[str]]
    ) -> None:
        """Log the prediction result and metrics"""
        try:
            if not mlflow.active_run():
                self.logger.warning("No active MLflow run to log to")
                return
            
            # Log core metrics
            mlflow.log_metric(MLflowConfig.CONFIDENCE_METRIC, result.get("confidence", 0.0))
            mlflow.log_metric(MLflowConfig.RESPONSE_TIME_METRIC, response_time_ms)
            
            # Log detected intent as tag for easy filtering
            detected_intent = result.get("detected_intent", "unknown")
            mlflow.set_tag(MLflowConfig.INTENT_TAG, detected_intent)
            
            # Log template matching info
            workflow_template = result.get("workflow_template_name", "")
            agent_template = result.get("agent_template_name", "")
            
            template_matched = 1 if (workflow_template and workflow_template != "TEMPLATE_NOT_FOUND") else 0
            mlflow.log_metric(MLflowConfig.TEMPLATE_MATCH_RATE, template_matched)
            
            # Log result details as parameters
            mlflow.log_param("requires_workflow", result.get("requires_workflow", False))
            mlflow.log_param("category_source", result.get("category_source", "unknown"))
            
            # Log prompt version
            prompt_signature = self.create_prompt_signature(signature_inputs)
            mlflow.set_tag(MLflowConfig.PROMPT_VERSION_TAG, prompt_signature)
            
            # Log available templates count
            mlflow.log_metric("available_workflow_templates", len(available_templates.get("workflows", [])))
            mlflow.log_metric("available_agent_templates", len(available_templates.get("agents", [])))
            
            # Log full result as artifact
            result_file = "prediction_result.json"
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            mlflow.log_artifact(result_file)
            os.remove(result_file)  # Clean up temp file
            
            self.logger.info(
                "Logged prediction result to MLflow",
                confidence=result.get("confidence"),
                intent=detected_intent,
                response_time=response_time_ms
            )
            
        except Exception as e:
            self.logger.error("Failed to log prediction result", error=str(e))
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error information"""
        try:
            if not mlflow.active_run():
                return
                
            mlflow.set_tag("error_occurred", True)
            mlflow.log_param("error_type", type(error).__name__)
            mlflow.log_param("error_message", str(error)[:500])  # Truncate long error messages
            
            # Log context that led to error
            for key, value in context.items():
                mlflow.log_param(f"error_context_{key}", str(value)[:200])
                
            self.logger.info("Logged error to MLflow", error_type=type(error).__name__)
            
        except Exception as e:
            self.logger.error("Failed to log error to MLflow", error=str(e))
    
    def end_run(self, status: str = "FINISHED") -> None:
        """End the current MLflow run"""
        try:
            if mlflow.active_run():
                mlflow.end_run(status=status)
                self.logger.info("Ended MLflow run", status=status)
        except Exception as e:
            self.logger.error("Failed to end MLflow run", error=str(e))
    
    def _get_dspy_version(self) -> str:
        """Get DSPy version for tracking"""
        try:
            import dspy
            return getattr(dspy, '__version__', 'unknown')
        except Exception:
            return 'unknown'
    
    def log_prompt_optimization_metrics(
        self,
        optimization_method: str,
        before_score: float,
        after_score: float,
        improvement: float,
        iteration: int
    ) -> None:
        """Log prompt optimization metrics"""
        try:
            mlflow.set_experiment(MLflowConfig.PROMPT_OPTIMIZATION_EXPERIMENT)
            
            with mlflow.start_run(nested=True):
                mlflow.log_param("optimization_method", optimization_method)
                mlflow.log_param("iteration", iteration)
                mlflow.log_metric("before_score", before_score)
                mlflow.log_metric("after_score", after_score)
                mlflow.log_metric("improvement", improvement)
                
                mlflow.set_tag("optimization_timestamp", datetime.now(timezone.utc).isoformat())
                
            self.logger.info(
                "Logged prompt optimization metrics",
                method=optimization_method,
                improvement=improvement
            )
            
        except Exception as e:
            self.logger.error("Failed to log optimization metrics", error=str(e))


# Global tracker instance
mlflow_tracker = DSPyMLflowTracker()