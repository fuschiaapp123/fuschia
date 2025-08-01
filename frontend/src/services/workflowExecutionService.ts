import { useAuthStore } from '@/store/authStore';

export interface ExecutionCreateRequest {
  workflow_template_id: string;
  organization_id?: string;
  execution_context?: Record<string, any>;
  priority?: number;
}

export interface TaskResponse {
  id: string;
  name: string;
  description: string;
  objective: string;
  completion_criteria: string;
  status: string;
  assigned_agent_id?: string;
  started_at?: string;
  completed_at?: string;
  dependencies: string[];
  context: Record<string, any>;
  results: Record<string, any>;
  human_feedback?: string;
}

export interface ExecutionResponse {
  id: string;
  workflow_template_id: string;
  organization_id?: string;
  status: string;
  current_tasks: string[];
  completed_tasks: string[];
  failed_tasks: string[];
  tasks: TaskResponse[];
  execution_context: Record<string, any>;
  human_approvals_pending: string[];
  human_feedback: Record<string, any>[];
  started_at: string;
  estimated_completion?: string;
  actual_completion?: string;
  initiated_by: string;
  agent_actions: Record<string, any>[];
  error_log: Record<string, any>[];
}

export interface ExecutionListResponse {
  executions: ExecutionResponse[];
  total_count: number;
}

export interface ExecutionStatsResponse {
  total_executions: number;
  status_breakdown: Record<string, number>;
  recent_executions: number;
  generated_at: string;
}

class WorkflowExecutionService {
  private baseUrl = 'http://localhost:8000/api/v1';

  private getHeaders(): HeadersInit {
    const token = useAuthStore.getState().token;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  /**
   * Execute a workflow template
   */
  async executeWorkflow(templateId: string, request: Omit<ExecutionCreateRequest, 'workflow_template_id'>): Promise<ExecutionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/${templateId}/execute`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          workflow_template_id: templateId,
          ...request
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      throw error;
    }
  }

  /**
   * List workflow executions
   */
  async listExecutions(params?: {
    status?: string;
    workflow_template_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<ExecutionListResponse> {
    try {
      const searchParams = new URLSearchParams();
      
      if (params?.status) searchParams.append('status', params.status);
      if (params?.workflow_template_id) searchParams.append('workflow_template_id', params.workflow_template_id);
      if (params?.limit) searchParams.append('limit', params.limit.toString());
      if (params?.offset) searchParams.append('offset', params.offset.toString());

      const response = await fetch(`${this.baseUrl}/executions/?${searchParams.toString()}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to list executions:', error);
      throw error;
    }
  }

  /**
   * Get a specific execution
   */
  async getExecution(executionId: string): Promise<ExecutionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get execution:', error);
      throw error;
    }
  }

  /**
   * Pause an execution
   */
  async pauseExecution(executionId: string): Promise<{ message: string; execution_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/pause`, {
        method: 'POST',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to pause execution:', error);
      throw error;
    }
  }

  /**
   * Resume an execution
   */
  async resumeExecution(executionId: string): Promise<{ message: string; execution_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/resume`, {
        method: 'POST',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to resume execution:', error);
      throw error;
    }
  }

  /**
   * Cancel an execution
   */
  async cancelExecution(executionId: string): Promise<{ message: string; execution_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/${executionId}/cancel`, {
        method: 'POST',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to cancel execution:', error);
      throw error;
    }
  }

  /**
   * Get execution statistics
   */
  async getExecutionStats(): Promise<ExecutionStatsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/executions/stats/overview`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to get execution stats:', error);
      throw error;
    }
  }

  /**
   * Get execution status display name
   */
  getStatusDisplayName(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': 'Pending',
      'running': 'Running',
      'paused': 'Paused',
      'completed': 'Completed',
      'failed': 'Failed',
      'cancelled': 'Cancelled'
    };
    
    return statusMap[status] || status;
  }

  /**
   * Get execution status color for UI
   */
  getStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'pending': 'text-yellow-600 bg-yellow-100',
      'running': 'text-blue-600 bg-blue-100',
      'paused': 'text-orange-600 bg-orange-100',
      'completed': 'text-green-600 bg-green-100',
      'failed': 'text-red-600 bg-red-100',
      'cancelled': 'text-gray-600 bg-gray-100'
    };
    
    return colorMap[status] || 'text-gray-600 bg-gray-100';
  }

  /**
   * Calculate execution duration
   */
  getExecutionDuration(startedAt: string, completedAt?: string): string {
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Get task completion percentage
   */
  getExecutionProgress(execution: ExecutionResponse): number {
    const totalTasks = execution.tasks.length;
    if (totalTasks === 0) return 0;
    
    const completedTasks = execution.completed_tasks.length;
    return Math.round((completedTasks / totalTasks) * 100);
  }
}

export const workflowExecutionService = new WorkflowExecutionService();