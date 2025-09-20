import React, { useState, useEffect } from 'react';
import {
  dspyEvaluationService,
  DSPyEvaluationConfig,
  DSPyEvaluationResult,
  DSPyExample,
  DSPyEvaluationMetric,
  DSPyOptimizationStrategy,
  DSPyEvaluationSummary
} from '../../services/dspyEvaluationService';
import { 
  Play, 
  Plus, 
  Trash2, 
  Settings, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle,
  Clock,
  Target,
  BarChart3,
  Sparkles,
  BookOpen,
  Save
} from 'lucide-react';

interface DSPyEvaluationPanelProps {
  taskId: string;
  taskLabel: string;
  isVisible: boolean;
  onClose: () => void;
}

interface ExampleFormData {
  input_text: string;
  expected_output: string;
  context?: string;
}

export const DSPyEvaluationPanel: React.FC<DSPyEvaluationPanelProps> = ({
  taskId,
  taskLabel,
  isVisible,
  onClose
}) => {
  // State
  const [config, setConfig] = useState<DSPyEvaluationConfig | null>(null);
  const [summary, setSummary] = useState<DSPyEvaluationSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'examples' | 'metrics' | 'results'>('overview');
  const [showExampleForm, setShowExampleForm] = useState(false);
  const [exampleFormData, setExampleFormData] = useState<ExampleFormData>({
    input_text: '',
    expected_output: '',
    context: ''
  });
  const [evaluationResults, setEvaluationResults] = useState<DSPyEvaluationResult[]>([]);
  const [optimizationStatus, setOptimizationStatus] = useState<any>(null);

  // Load data
  useEffect(() => {
    if (isVisible && taskId) {
      loadData();
    }
  }, [isVisible, taskId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load summary
      const summaryData = await dspyEvaluationService.getTaskEvaluationSummary(taskId);
      setSummary(summaryData);

      // Load config if it exists
      const configs = await dspyEvaluationService.listEvaluationConfigs(taskId);
      if (configs.length > 0) {
        setConfig(configs[0]);
      }

      // Load results
      const results = await dspyEvaluationService.listEvaluationResults(taskId, 10, 0);
      setEvaluationResults(results);

      // Load optimization status
      const status = await dspyEvaluationService.getOptimizationStatus(taskId);
      setOptimizationStatus(status);
    } catch (error) {
      console.error('Failed to load DSPy data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createInitialConfig = async () => {
    setIsLoading(true);
    try {
      const newConfig = await dspyEvaluationService.createEvaluationConfig({
        task_id: taskId,
        metrics: [DSPyEvaluationMetric.ACCURACY],
        optimization_strategy: DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT,
        examples: []
      });
      setConfig(newConfig);
      await loadData();
    } catch (error) {
      console.error('Failed to create config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const addExample = async () => {
    if (!config || !exampleFormData.input_text || !exampleFormData.expected_output) {
      return;
    }

    try {
      const newExample = dspyEvaluationService.createExample(
        { input_text: exampleFormData.input_text, context: exampleFormData.context },
        { output: exampleFormData.expected_output }
      );

      const updatedConfig = await dspyEvaluationService.addExamples(config.id, [newExample]);
      setConfig(updatedConfig);

      // Reset form
      setExampleFormData({ input_text: '', expected_output: '', context: '' });
      setShowExampleForm(false);
      await loadData();
    } catch (error) {
      console.error('Failed to add example:', error);
    }
  };

  const removeExample = async (exampleId: string) => {
    if (!config) return;

    try {
      const updatedConfig = await dspyEvaluationService.removeExample(config.id, exampleId);
      setConfig(updatedConfig);
      await loadData();
    } catch (error) {
      console.error('Failed to remove example:', error);
    }
  };

  const runEvaluation = async (withOptimization: boolean = false) => {
    if (!config) return;

    setIsLoading(true);
    try {
      await dspyEvaluationService.runEvaluation({
        evaluation_config_id: config.id,
        run_optimization: withOptimization,
        save_results: true
      });
      
      // Reload data after a short delay
      setTimeout(loadData, 2000);
    } catch (error) {
      console.error('Failed to run evaluation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runOptimization = async () => {
    if (!config) return;

    setIsLoading(true);
    try {
      await dspyEvaluationService.optimizeTask({
        task_id: taskId,
        evaluation_config_id: config.id,
        optimization_strategy: config.optimization_strategy,
        optimization_params: config.optimization_params,
        max_iterations: 50,
        timeout_minutes: 30,
        target_metric: config.metrics[0] || DSPyEvaluationMetric.ACCURACY,
        use_cached_results: true,
        save_intermediate_results: true
      });

      // Reload data after a short delay
      setTimeout(loadData, 2000);
    } catch (error) {
      console.error('Failed to run optimization:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">DSPy Evaluation & Optimization</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">Task: {taskLabel}</p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
          <p className="text-sm text-gray-600 mt-2">Loading...</p>
        </div>
      )}

      {/* No Config State */}
      {!isLoading && !config && (
        <div className="p-6 text-center">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">DSPy Evaluation Not Set Up</h4>
          <p className="text-sm text-gray-600 mb-4">
            Set up DSPy evaluation to optimize this task's performance with examples and metrics.
          </p>
          <button
            onClick={createInitialConfig}
            className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Set Up DSPy Evaluation
          </button>
        </div>
      )}

      {/* Main Content */}
      {!isLoading && config && (
        <>
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-6 px-4">
              {[
                { key: 'overview', label: 'Overview', icon: BarChart3 },
                { key: 'examples', label: 'Examples', icon: BookOpen },
                { key: 'metrics', label: 'Metrics', icon: Target },
                { key: 'results', label: 'Results', icon: TrendingUp }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key as any)}
                  className={`flex items-center space-x-2 py-3 border-b-2 text-sm font-medium transition-colors ${
                    activeTab === key
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-4">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center space-x-2">
                      <BookOpen className="h-5 w-5 text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">Examples</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-700 mt-2">{config.examples.length}</p>
                    <p className="text-xs text-blue-600">Training examples</p>
                  </div>

                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-2">
                      <Target className="h-5 w-5 text-green-600" />
                      <span className="text-sm font-medium text-green-900">Best Score</span>
                    </div>
                    <p className="text-2xl font-bold text-green-700 mt-2">
                      {summary?.best_score ? dspyEvaluationService.formatScore(summary.best_score) : 'N/A'}
                    </p>
                    <p className="text-xs text-green-600">
                      {summary?.latest_metric || 'No evaluations yet'}
                    </p>
                  </div>

                  <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="h-5 w-5 text-purple-600" />
                      <span className="text-sm font-medium text-purple-900">Trend</span>
                    </div>
                    <div className="flex items-center space-x-2 mt-2">
                      <span className="text-lg">
                        {summary?.improvement_trend 
                          ? dspyEvaluationService.getTrendIcon(summary.improvement_trend)
                          : '➡️'
                        }
                      </span>
                      <span className="text-sm font-medium text-purple-700 capitalize">
                        {summary?.improvement_trend || 'No trend'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3">
                  <button
                    onClick={() => runEvaluation(false)}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Run Evaluation
                  </button>
                  
                  <button
                    onClick={() => runEvaluation(true)}
                    className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Evaluate & Optimize
                  </button>
                  
                  <button
                    onClick={runOptimization}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Optimize Only
                  </button>
                </div>

                {/* Optimization Status */}
                {optimizationStatus && optimizationStatus.status !== 'not_started' && (
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-lg">
                        {dspyEvaluationService.getStatusIcon(optimizationStatus.status)}
                      </span>
                      <span className="font-medium">Optimization Status</span>
                    </div>
                    <p className="text-sm text-gray-600 capitalize">
                      Status: {optimizationStatus.status.replace('_', ' ')}
                    </p>
                    {optimizationStatus.progress && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-purple-600 h-2 rounded-full transition-all"
                            style={{ width: `${optimizationStatus.progress * 100}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {Math.round(optimizationStatus.progress * 100)}% complete
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Examples Tab */}
            {activeTab === 'examples' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-lg font-medium">Training Examples</h4>
                  <button
                    onClick={() => setShowExampleForm(true)}
                    className="flex items-center px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Example
                  </button>
                </div>

                {/* Example Form */}
                {showExampleForm && (
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <h5 className="font-medium mb-3">Add Training Example</h5>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Input Text
                        </label>
                        <textarea
                          value={exampleFormData.input_text}
                          onChange={(e) => setExampleFormData({ ...exampleFormData, input_text: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          rows={2}
                          placeholder="Enter the input for this example..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Expected Output
                        </label>
                        <textarea
                          value={exampleFormData.expected_output}
                          onChange={(e) => setExampleFormData({ ...exampleFormData, expected_output: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          rows={2}
                          placeholder="Enter the expected output..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Context (Optional)
                        </label>
                        <input
                          type="text"
                          value={exampleFormData.context || ''}
                          onChange={(e) => setExampleFormData({ ...exampleFormData, context: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="Additional context..."
                        />
                      </div>

                      <div className="flex space-x-2">
                        <button
                          onClick={addExample}
                          className="flex items-center px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
                        >
                          <Save className="h-4 w-4 mr-1" />
                          Save Example
                        </button>
                        <button
                          onClick={() => setShowExampleForm(false)}
                          className="px-3 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Examples List */}
                <div className="space-y-3">
                  {config.examples.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <BookOpen className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                      <p>No examples added yet</p>
                      <p className="text-sm">Add training examples to improve DSPy optimization</p>
                    </div>
                  ) : (
                    config.examples.map((example, index) => (
                      <div key={example.id} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-sm font-medium text-gray-500">Example {index + 1}</span>
                              <span className="text-xs text-gray-400">ID: {example.id.slice(0, 8)}...</span>
                            </div>
                            
                            <div className="space-y-2">
                              <div>
                                <span className="text-xs font-medium text-blue-600">INPUT:</span>
                                <p className="text-sm text-gray-700 bg-blue-50 p-2 rounded mt-1">
                                  {example.input_data.input_text || JSON.stringify(example.input_data)}
                                </p>
                              </div>
                              
                              <div>
                                <span className="text-xs font-medium text-green-600">EXPECTED:</span>
                                <p className="text-sm text-gray-700 bg-green-50 p-2 rounded mt-1">
                                  {example.expected_output.output || JSON.stringify(example.expected_output)}
                                </p>
                              </div>
                            </div>
                          </div>
                          
                          <button
                            onClick={() => removeExample(example.id)}
                            className="ml-4 p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Metrics Tab */}
            {activeTab === 'metrics' && (
              <div className="space-y-4">
                <h4 className="text-lg font-medium">Evaluation Metrics</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {config.metrics.map((metric) => (
                    <div key={metric} className="bg-gray-50 p-4 rounded-lg border">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span className="font-medium">{dspyEvaluationService.getMetricDisplayName(metric)}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {metric === DSPyEvaluationMetric.ACCURACY && 'Measures exact match accuracy'}
                        {metric === DSPyEvaluationMetric.SEMANTIC_SIMILARITY && 'Measures semantic similarity of outputs'}
                        {metric === DSPyEvaluationMetric.BLEU && 'BLEU score for text generation quality'}
                        {metric === DSPyEvaluationMetric.ROUGE && 'ROUGE score for summarization quality'}
                        {metric === DSPyEvaluationMetric.F1_SCORE && 'F1 score for classification tasks'}
                        {metric === DSPyEvaluationMetric.PRECISION && 'Precision for classification tasks'}
                        {metric === DSPyEvaluationMetric.RECALL && 'Recall for classification tasks'}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="bg-gray-50 p-4 rounded-lg border">
                  <h5 className="font-medium mb-2">Optimization Strategy</h5>
                  <div className="flex items-center space-x-2">
                    <Settings className="h-5 w-5 text-purple-500" />
                    <span className="font-medium">
                      {dspyEvaluationService.getStrategyDisplayName(config.optimization_strategy)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {config.optimization_strategy === DSPyOptimizationStrategy.BOOTSTRAP_FEW_SHOT && 
                      'Uses few-shot examples to optimize prompts'}
                    {config.optimization_strategy === DSPyOptimizationStrategy.COPRO && 
                      'Coordinate ascent prompt optimization'}
                    {config.optimization_strategy === DSPyOptimizationStrategy.MIPRO && 
                      'Multi-prompt instruction optimization'}
                  </p>
                </div>
              </div>
            )}

            {/* Results Tab */}
            {activeTab === 'results' && (
              <div className="space-y-4">
                <h4 className="text-lg font-medium">Evaluation Results</h4>
                
                {evaluationResults.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>No evaluation results yet</p>
                    <p className="text-sm">Run an evaluation to see results</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {evaluationResults.map((result) => (
                      <div key={result.id} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">
                              {dspyEvaluationService.getStatusIcon(result.status)}
                            </span>
                            <span className="font-medium">Evaluation {result.id.slice(0, 8)}...</span>
                          </div>
                          <span className="text-sm text-gray-500">
                            {new Date(result.created_at).toLocaleString()}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mb-3">
                          <div>
                            <span className="text-sm text-gray-500">Execution Time</span>
                            <p className="font-medium">{result.execution_time_seconds.toFixed(2)}s</p>
                          </div>
                          <div>
                            <span className="text-sm text-gray-500">Model</span>
                            <p className="font-medium">{result.model_used}</p>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <span className="text-sm font-medium text-gray-700">Scores:</span>
                          {Object.entries(result.metric_scores).map(([metric, score]) => (
                            <div key={metric} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                              <span className="text-sm text-gray-600 capitalize">{metric}</span>
                              <span className="font-medium text-purple-600">
                                {dspyEvaluationService.formatScore(score)}
                              </span>
                            </div>
                          ))}
                        </div>
                        
                        {result.optimized_prompt && (
                          <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded">
                            <span className="text-sm font-medium text-purple-700">Optimized Prompt:</span>
                            <p className="text-sm text-purple-600 mt-1 font-mono">
                              {result.optimized_prompt.length > 200 
                                ? result.optimized_prompt.slice(0, 200) + '...'
                                : result.optimized_prompt
                              }
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};