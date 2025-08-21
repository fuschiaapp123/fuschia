"""
MLflow Dashboard and Monitoring utilities for DSPy Intent Detection
"""

import mlflow
import mlflow.tracking
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import structlog
from app.services.mlflow_config import MLflowConfig

logger = structlog.get_logger()


class IntentDetectionDashboard:
    """Dashboard and analytics for DSPy intent detection using MLflow"""
    
    def __init__(self):
        self.client = mlflow.tracking.MlflowClient()
        self.logger = logger.bind(component="IntentDetectionDashboard")
    
    def get_experiment_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get overview of intent detection performance over the last N days"""
        try:
            experiment = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            if not experiment:
                return {"error": "Experiment not found"}
            
            # Get runs from the last N days
            since_date = datetime.now() - timedelta(days=days)
            since_timestamp = int(since_date.timestamp() * 1000)
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.start_time >= {since_timestamp}",
                order_by=["start_time DESC"]
            )
            
            if runs.empty:
                return {"message": "No runs found in the specified period"}
            
            # Calculate key metrics
            total_runs = len(runs)
            successful_runs = len(runs[runs['status'] == 'FINISHED'])
            failed_runs = len(runs[runs['status'] == 'FAILED'])
            
            # Average metrics
            avg_confidence = runs['metrics.confidence_score'].mean() if 'metrics.confidence_score' in runs.columns else 0
            avg_response_time = runs['metrics.response_time_ms'].mean() if 'metrics.response_time_ms' in runs.columns else 0
            template_match_rate = runs['metrics.template_match_rate'].mean() if 'metrics.template_match_rate' in runs.columns else 0
            
            # Intent distribution
            intent_distribution = {}
            if 'tags.detected_intent' in runs.columns:
                intent_counts = runs['tags.detected_intent'].value_counts()
                intent_distribution = intent_counts.to_dict()
            
            # User role analysis
            user_role_distribution = {}
            if 'tags.user_role' in runs.columns:
                role_counts = runs['tags.user_role'].value_counts()
                user_role_distribution = role_counts.to_dict()
            
            # Module usage
            module_distribution = {}
            if 'tags.current_module' in runs.columns:
                module_counts = runs['tags.current_module'].value_counts()
                module_distribution = module_counts.to_dict()
            
            overview = {
                "period_days": days,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                "avg_confidence": round(avg_confidence, 3),
                "avg_response_time_ms": round(avg_response_time, 2),
                "template_match_rate": round(template_match_rate * 100, 1),
                "intent_distribution": intent_distribution,
                "user_role_distribution": user_role_distribution,
                "module_distribution": module_distribution,
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info("Generated experiment overview", total_runs=total_runs, days=days)
            return overview
            
        except Exception as e:
            self.logger.error("Failed to generate experiment overview", error=str(e))
            return {"error": str(e)}
    
    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time"""
        try:
            experiment = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            if not experiment:
                return {"error": "Experiment not found"}
            
            since_date = datetime.now() - timedelta(days=days)
            since_timestamp = int(since_date.timestamp() * 1000)
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.start_time >= {since_timestamp}",
                order_by=["start_time ASC"]
            )
            
            if runs.empty:
                return {"message": "No runs found for trend analysis"}
            
            # Convert start_time to datetime
            runs['start_datetime'] = pd.to_datetime(runs['start_time'], unit='ms')
            runs['date'] = runs['start_datetime'].dt.date
            
            # Daily aggregations
            daily_stats = runs.groupby('date').agg({
                'metrics.confidence_score': ['mean', 'std', 'count'],
                'metrics.response_time_ms': ['mean', 'std'],
                'metrics.template_match_rate': 'mean'
            }).round(3)
            
            # Convert to list of dictionaries for easier consumption
            trends = []
            for date, row in daily_stats.iterrows():
                trends.append({
                    "date": date.isoformat(),
                    "avg_confidence": row[('metrics.confidence_score', 'mean')],
                    "confidence_std": row[('metrics.confidence_score', 'std')],
                    "request_count": row[('metrics.confidence_score', 'count')],
                    "avg_response_time_ms": row[('metrics.response_time_ms', 'mean')],
                    "response_time_std": row[('metrics.response_time_ms', 'std')],
                    "template_match_rate": row[('metrics.template_match_rate', 'mean')]
                })
            
            return {
                "period_days": days,
                "trends": trends,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to generate performance trends", error=str(e))
            return {"error": str(e)}
    
    def get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analyze errors and failure patterns"""
        try:
            experiment = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            if not experiment:
                return {"error": "Experiment not found"}
            
            since_date = datetime.now() - timedelta(days=days)
            since_timestamp = int(since_date.timestamp() * 1000)
            
            # Get failed runs
            failed_runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"attributes.start_time >= {since_timestamp} AND tags.error_occurred = 'True'",
                order_by=["start_time DESC"]
            )
            
            if failed_runs.empty:
                return {"message": "No errors found in the specified period", "error_count": 0}
            
            # Error type analysis
            error_types = {}
            if 'params.error_type' in failed_runs.columns:
                error_type_counts = failed_runs['params.error_type'].value_counts()
                error_types = error_type_counts.to_dict()
            
            # Error context analysis
            error_contexts = []
            for _, run in failed_runs.head(10).iterrows():  # Get latest 10 errors
                context = {
                    "run_id": run.get('run_id', 'unknown'),
                    "timestamp": pd.to_datetime(run.get('start_time', 0), unit='ms').isoformat(),
                    "error_type": run.get('params.error_type', 'unknown'),
                    "error_message": run.get('params.error_message', 'no message')[:200],
                    "user_role": run.get('tags.user_role', 'unknown'),
                    "module": run.get('tags.current_module', 'unknown'),
                    "tab": run.get('tags.current_tab', 'unknown')
                }
                error_contexts.append(context)
            
            return {
                "period_days": days,
                "total_errors": len(failed_runs),
                "error_types": error_types,
                "recent_errors": error_contexts,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to generate error analysis", error=str(e))
            return {"error": str(e)}
    
    def get_model_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance across different model configurations"""
        try:
            experiment = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            if not experiment:
                return {"error": "Experiment not found"}
            
            # Get all successful runs
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string="attributes.status = 'FINISHED'",
                order_by=["start_time DESC"],
                max_results=1000
            )
            
            if runs.empty:
                return {"message": "No successful runs found"}
            
            # Group by model name
            model_stats = runs.groupby('params.model_name').agg({
                'metrics.confidence_score': ['mean', 'std', 'count'],
                'metrics.response_time_ms': ['mean', 'std'],
                'metrics.template_match_rate': 'mean'
            }).round(3)
            
            model_comparison = []
            for model_name, row in model_stats.iterrows():
                model_comparison.append({
                    "model_name": model_name,
                    "avg_confidence": row[('metrics.confidence_score', 'mean')],
                    "confidence_std": row[('metrics.confidence_score', 'std')],
                    "run_count": row[('metrics.confidence_score', 'count')],
                    "avg_response_time_ms": row[('metrics.response_time_ms', 'mean')],
                    "response_time_std": row[('metrics.response_time_ms', 'std')],
                    "template_match_rate": row[('metrics.template_match_rate', 'mean')]
                })
            
            # Sort by confidence score
            model_comparison.sort(key=lambda x: x['avg_confidence'], reverse=True)
            
            return {
                "model_comparison": model_comparison,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to generate model comparison", error=str(e))
            return {"error": str(e)}
    
    def get_prompt_version_analysis(self) -> Dict[str, Any]:
        """Analyze performance across different prompt versions"""
        try:
            experiment = mlflow.get_experiment_by_name(MLflowConfig.INTENT_CLASSIFICATION_EXPERIMENT)
            if not experiment:
                return {"error": "Experiment not found"}
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string="attributes.status = 'FINISHED'",
                order_by=["start_time DESC"],
                max_results=1000
            )
            
            if runs.empty or 'tags.prompt_version' not in runs.columns:
                return {"message": "No prompt version data available"}
            
            # Group by prompt version
            prompt_stats = runs.groupby('tags.prompt_version').agg({
                'metrics.confidence_score': ['mean', 'std', 'count'],
                'metrics.response_time_ms': ['mean', 'std'],
                'metrics.template_match_rate': 'mean'
            }).round(3)
            
            prompt_analysis = []
            for prompt_version, row in prompt_stats.iterrows():
                # Get latest run with this prompt version for additional context
                latest_run = runs[runs['tags.prompt_version'] == prompt_version].iloc[0]
                
                prompt_analysis.append({
                    "prompt_version": prompt_version,
                    "avg_confidence": row[('metrics.confidence_score', 'mean')],
                    "confidence_std": row[('metrics.confidence_score', 'std')],
                    "run_count": row[('metrics.confidence_score', 'count')],
                    "avg_response_time_ms": row[('metrics.response_time_ms', 'mean')],
                    "template_match_rate": row[('metrics.template_match_rate', 'mean')],
                    "last_used": pd.to_datetime(latest_run['start_time'], unit='ms').isoformat(),
                    "dspy_version": latest_run.get('tags.dspy_version', 'unknown')
                })
            
            # Sort by confidence score
            prompt_analysis.sort(key=lambda x: x['avg_confidence'], reverse=True)
            
            return {
                "prompt_analysis": prompt_analysis,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to generate prompt analysis", error=str(e))
            return {"error": str(e)}
    
    def export_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            report = {
                "report_period_days": days,
                "generated_at": datetime.now().isoformat(),
                "overview": self.get_experiment_overview(days),
                "trends": self.get_performance_trends(days),
                "errors": self.get_error_analysis(days),
                "model_comparison": self.get_model_performance_comparison(),
                "prompt_analysis": self.get_prompt_version_analysis()
            }
            
            self.logger.info("Generated comprehensive performance report", days=days)
            return report
            
        except Exception as e:
            self.logger.error("Failed to generate performance report", error=str(e))
            return {"error": str(e)}


# Global dashboard instance
dashboard = IntentDetectionDashboard()