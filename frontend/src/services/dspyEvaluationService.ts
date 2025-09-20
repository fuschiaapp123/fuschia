/**
 * DSPy Evaluation Service
 * 
 * Service for managing DSPy evaluation and optimization functionality,
 * including examples, metrics, and optimization strategies.
 */

import { api as apiClient } from '@/utils/api';

// Types
export interface DSPyExample {
  id: string;
  input_data: Record<string, any>;
  expected_output: Record<string, any>;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface DSPyEvaluationConfig {
  id: string;
  task_id: string;
  examples: DSPyExample[];
  test_examples: DSPyExample[];
  metrics: DSPyEvaluationMetric[];
  custom_metric_code?: string;
  optimization_strategy: DSPyOptimizationStrategy;
  optimization_params: Record<string, any>;
  train_test_split: number;
  cross_validation_folds: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface DSPyEvaluationResult {
  id: string;
  evaluation_config_id: string;
  task_id: string;
  metric_scores: Record<string, number>;
  detailed_results: Array<Record<string, any>>;
  optimized_prompt?: string;
  optimization_history: Array<Record<string, any>>;
  execution_time_seconds: number;
  model_used: string;
  dspy_version: string;
  status: string;
  error_message?: string;
  artifacts: Record<string, any>;
  created_at: string;
}

export interface DSPyEvaluationSummary {
  task_id: string;
  task_label: string;
  latest_evaluation_id?: string;
  latest_score?: number;
  latest_metric?: string;
  evaluation_count: number;
  best_score?: number;
  improvement_trend?: string;
  optimization_status: string;
  last_optimized_at?: string;
  total_examples: number;
  enabled_metrics: string[];
}

export enum DSPyEvaluationMetric {
  ACCURACY = 'accuracy',
  PRECISION = 'precision',
  RECALL = 'recall',
  F1_SCORE = 'f1_score',
  BLEU = 'bleu',
  ROUGE = 'rouge',
  SEMANTIC_SIMILARITY = 'semantic_similarity',
  CUSTOM = 'custom'
}

export enum DSPyOptimizationStrategy {
  BOOTSTRAP_FEW_SHOT = 'bootstrap_few_shot',
  COPRO = 'copro',
  MIPRO = 'mipro',
  ENSEMBLE = 'ensemble',
  RANDOM_SEARCH = 'random_search',
  GRID_SEARCH = 'grid_search'
}

// Request types
export interface CreateEvaluationConfigRequest {
  task_id: string;
  metrics: DSPyEvaluationMetric[];
  optimization_strategy: DSPyOptimizationStrategy;
  examples: DSPyExample[];
}

export interface UpdateEvaluationConfigRequest {
  examples?: DSPyExample[];
  metrics?: DSPyEvaluationMetric[];
  optimization_strategy?: DSPyOptimizationStrategy;
  optimization_params?: Record<string, any>;
}

export interface RunEvaluationRequest {
  evaluation_config_id: string;
  run_optimization: boolean;
  save_results: boolean;
}

export interface OptimizationRequest {
  task_id: string;
  evaluation_config_id: string;
  optimization_strategy: DSPyOptimizationStrategy;
  optimization_params: Record<string, any>;
  max_iterations: number;
  timeout_minutes: number;
  target_metric: DSPyEvaluationMetric;
  target_score?: number;
  use_cached_results: boolean;
  save_intermediate_results: boolean;
}

class DSPyEvaluationService {
  
  // Evaluation Configuration Methods
  async createEvaluationConfig(request: CreateEvaluationConfigRequest): Promise<DSPyEvaluationConfig> {
    const response = await apiClient.post('/dspy-evaluation/configs', request);
    return response.data.config;
  }

  async getEvaluationConfig(configId: string): Promise<DSPyEvaluationConfig> {
    const response = await apiClient.get(`/dspy-evaluation/configs/${configId}`);
    return response.data.config;
  }

  async updateEvaluationConfig(
    configId: string,
    request: UpdateEvaluationConfigRequest
  ): Promise<DSPyEvaluationConfig> {
    const response = await apiClient.put(`/dspy-evaluation/configs/${configId}`, request);
    return response.data.config;
  }

  async listEvaluationConfigs(taskId?: string): Promise<DSPyEvaluationConfig[]> {
    const params = taskId ? { task_id: taskId } : {};
    const response = await apiClient.get('/dspy-evaluation/configs', { params });
    return response.data;
  }

  async deleteEvaluationConfig(configId: string): Promise<void> {
    await apiClient.delete(`/dspy-evaluation/configs/${configId}`);
  }

  // Example Management Methods
  async addExamples(configId: string, examples: DSPyExample[]): Promise<DSPyEvaluationConfig> {
    const response = await apiClient.post(`/dspy-evaluation/configs/${configId}/examples`, {
      examples
    });
    return response.data.config;
  }

  async removeExample(configId: string, exampleId: string): Promise<DSPyEvaluationConfig> {
    const response = await apiClient.delete(
      `/dspy-evaluation/configs/${configId}/examples/${exampleId}`
    );
    return response.data.config;
  }

  // Evaluation Execution Methods
  async runEvaluation(request: RunEvaluationRequest): Promise<DSPyEvaluationResult> {
    const response = await apiClient.post('/dspy-evaluation/evaluate', request);
    return response.data.result;
  }

  async optimizeTask(request: OptimizationRequest): Promise<DSPyEvaluationResult> {
    const response = await apiClient.post('/dspy-evaluation/optimize', request);
    return response.data.result;
  }

  // Results and Status Methods
  async getEvaluationResult(resultId: string): Promise<DSPyEvaluationResult> {
    const response = await apiClient.get(`/dspy-evaluation/results/${resultId}`);
    return response.data.result;
  }

  async listEvaluationResults(
    taskId?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<DSPyEvaluationResult[]> {
    const params = { limit, offset };
    if (taskId) (params as any).task_id = taskId;
    
    const response = await apiClient.get('/dspy-evaluation/results', { params });
    return response.data;
  }

  async getTaskEvaluationSummary(taskId: string): Promise<DSPyEvaluationSummary> {
    const response = await apiClient.get(`/dspy-evaluation/tasks/${taskId}/summary`);
    return response.data;
  }

  async getOptimizationStatus(taskId: string): Promise<any> {
    const response = await apiClient.get(`/dspy-evaluation/tasks/${taskId}/optimization-status`);
    return response.data;
  }

  // Utility Methods
  async getAvailableMetrics(): Promise<string[]> {
    const response = await apiClient.get('/dspy-evaluation/metrics');
    return response.data;
  }

  async getOptimizationStrategies(): Promise<string[]> {
    const response = await apiClient.get('/dspy-evaluation/optimization-strategies');
    return response.data;
  }

  async validateEvaluationConfig(configId: string): Promise<any> {
    const response = await apiClient.post(`/dspy-evaluation/configs/${configId}/validate`);
    return response.data;
  }

  // Helper Methods
  createExample(
    inputData: Record<string, any>,
    expectedOutput: Record<string, any>,
    metadata?: Record<string, any>
  ): DSPyExample {
    return {
      id: crypto.randomUUID(),
      input_data: inputData,
      expected_output: expectedOutput,
      metadata: metadata || {},
      created_at: new Date().toISOString()
    };
  }

  getMetricDisplayName(metric: DSPyEvaluationMetric): string {
    const displayNames = {
      [DSPyEvaluationMetric.ACCURACY]: 'Accuracy',
      [DSPyEvaluationMetric.PRECISION]: 'Precision',
      [DSPyEvaluationMetric.RECALL]: 'Recall',
      [DSPyEvaluationMetric.F1_SCORE]: 'F1 Score',
      [DSPyEvaluationMetric.BLEU]: 'BLEU Score',
      [DSPyEvaluationMetric.ROUGE]: 'ROUGE Score',
      [DSPyEvaluationMetric.SEMANTIC_SIMILARITY]: 'Semantic Similarity',
      [DSPyEvaluationMetric.CUSTOM]: 'Custom Metric'
    };
    return displayNames[metric] || metric;
  }

  getStrategyDisplayName(strategy: DSPyOptimizationStrategy): string {
    const displayNames = {
      [DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT]: 'Bootstrap Few-Shot',
      [DSPyOptimizationStrategy.COPRO]: 'COPRO',
      [DSPyOptimizationStrategy.MIPRO]: 'MIPRO',
      [DSPyOptimizationStrategy.ENSEMBLE]: 'Ensemble',
      [DSPyOptimizationStrategy.RANDOM_SEARCH]: 'Random Search',
      [DSPyOptimizationStrategy.GRID_SEARCH]: 'Grid Search'
    };
    return displayNames[strategy] || strategy;
  }

  formatScore(score: number): string {
    return (score * 100).toFixed(1) + '%';
  }

  getStatusColor(status: string): string {
    const colors = {
      'completed': 'green',
      'running': 'blue',
      'optimization_started': 'yellow',
      'failed': 'red',
      'not_started': 'gray'
    };
    return colors[status as keyof typeof colors] || 'gray';
  }

  getStatusIcon(status: string): string {
    const icons = {
      'completed': '✅',
      'running': '🔄',
      'optimization_started': '⚡',
      'failed': '❌',
      'not_started': '⚪'
    };
    return icons[status as keyof typeof icons] || '⚪';
  }

  getTrendIcon(trend: string): string {
    const icons = {
      'improving': '📈',
      'declining': '📉',
      'stable': '➡️'
    };
    return icons[trend as keyof typeof icons] || '➡️';
  }
}

export const dspyEvaluationService = new DSPyEvaluationService();