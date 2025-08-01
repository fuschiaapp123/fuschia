import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Play, Pause, Square, RotateCcw, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { workflowExecutionService, ExecutionResponse, ExecutionListResponse } from '@/services/workflowExecutionService';

const WorkflowExecutions: React.FC = () => {
  const [executions, setExecutions] = useState<ExecutionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  const loadExecutions = useCallback(async () => {
    try {
      setError(null);
      const params = selectedStatus ? { status: selectedStatus } : undefined;
      const response: ExecutionListResponse = await workflowExecutionService.listExecutions(params);
      setExecutions(response.executions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load executions');
      console.error('Failed to load executions:', err);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [selectedStatus]);

  useEffect(() => {
    loadExecutions();
  }, [loadExecutions]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadExecutions();
  }, [loadExecutions]);

  const handleStatusFilter = useCallback((status: string) => {
    setSelectedStatus(status);
    setIsLoading(true);
  }, []);

  const handleExecutionAction = useCallback(async (executionId: string, action: 'pause' | 'resume' | 'cancel') => {
    try {
      switch (action) {
        case 'pause':
          await workflowExecutionService.pauseExecution(executionId);
          break;
        case 'resume':
          await workflowExecutionService.resumeExecution(executionId);
          break;
        case 'cancel':
          await workflowExecutionService.cancelExecution(executionId);
          break;
      }
      
      // Refresh the list
      await loadExecutions();
    } catch (err) {
      alert(`Failed to ${action} execution: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [loadExecutions]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'running':
        return <Play className="w-4 h-4" />;
      case 'paused':
        return <Pause className="w-4 h-4" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'failed':
        return <XCircle className="w-4 h-4" />;
      case 'cancelled':
        return <Square className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (isLoading && !refreshing) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fuschia-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading workflow executions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-medium mb-2">Failed to load executions</p>
          <p className="text-gray-600 text-sm mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-fuschia-600 text-white rounded-lg hover:bg-fuschia-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflow Executions</h1>
          <p className="text-gray-600 mt-1">Monitor and manage your workflow executions</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 bg-fuschia-600 text-white rounded-lg hover:bg-fuschia-700 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Status Filter */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => handleStatusFilter('')}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            selectedStatus === '' 
              ? 'bg-fuschia-100 text-fuschia-800' 
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        {['pending', 'running', 'paused', 'completed', 'failed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => handleStatusFilter(status)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedStatus === status 
                ? 'bg-fuschia-100 text-fuschia-800' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {workflowExecutionService.getStatusDisplayName(status)}
          </button>
        ))}
      </div>

      {/* Executions List */}
      {executions.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Play className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No executions found</h3>
          <p className="text-gray-600">
            {selectedStatus 
              ? `No executions with status "${workflowExecutionService.getStatusDisplayName(selectedStatus)}"` 
              : 'Start executing workflows from the Process Designer to see them here.'}
          </p>
        </div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Execution
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {executions.map((execution) => {
                  const progress = workflowExecutionService.getExecutionProgress(execution);
                  const duration = workflowExecutionService.getExecutionDuration(
                    execution.started_at, 
                    execution.actual_completion
                  );
                  
                  return (
                    <tr key={execution.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {execution.id.substring(0, 8)}...
                          </div>
                          <div className="text-sm text-gray-500">
                            {execution.tasks.length} tasks
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`inline-flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium ${workflowExecutionService.getStatusColor(execution.status)}`}>
                          {getStatusIcon(execution.status)}
                          <span>{workflowExecutionService.getStatusDisplayName(execution.status)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-fuschia-600 h-2 rounded-full" 
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-700">{progress}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(execution.started_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {duration}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          {execution.status === 'running' && (
                            <button
                              onClick={() => handleExecutionAction(execution.id, 'pause')}
                              className="text-orange-600 hover:text-orange-900 transition-colors"
                              title="Pause execution"
                            >
                              <Pause className="w-4 h-4" />
                            </button>
                          )}
                          {execution.status === 'paused' && (
                            <button
                              onClick={() => handleExecutionAction(execution.id, 'resume')}
                              className="text-green-600 hover:text-green-900 transition-colors"
                              title="Resume execution"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          {['running', 'paused', 'pending'].includes(execution.status) && (
                            <button
                              onClick={() => {
                                if (confirm('Are you sure you want to cancel this execution?')) {
                                  handleExecutionAction(execution.id, 'cancel');
                                }
                              }}
                              className="text-red-600 hover:text-red-900 transition-colors"
                              title="Cancel execution"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowExecutions;