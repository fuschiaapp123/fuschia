import { Node, Edge } from '@xyflow/react';
import { useAuthStore } from '@/store/authStore';

export interface WorkflowSaveRequest {
  name: string;
  description: string;
  category: string;
  nodes: Node[];
  edges: Edge[];
  complexity?: 'simple' | 'medium' | 'advanced';
  estimatedTime?: string;
  tags?: string[];
}

export interface WorkflowSaveResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  template_type: string;
  created_at: string;
  status: string;
}

class WorkflowService {
  private baseUrl = 'http://localhost:8000/api/v1';

  /**
   * Save workflow to PostgreSQL database
   */
  async saveWorkflowToDatabase(workflowData: WorkflowSaveRequest): Promise<WorkflowSaveResponse> {
    try {
      // Get auth token
      const token = useAuthStore.getState().token;
      
      // Prepare the request payload
      const payload = {
        name: workflowData.name,
        description: workflowData.description,
        category: workflowData.category,
        template_type: 'workflow',
        complexity: workflowData.complexity || 'medium',
        estimated_time: workflowData.estimatedTime || 'Variable',
        tags: workflowData.tags || [workflowData.category, 'Custom'],
        preview_steps: this.extractPreviewSteps(workflowData.nodes),
        template_data: {
          nodes: workflowData.nodes.map(node => ({
            ...node,
            selected: false,
            dragging: false,
          })),
          edges: workflowData.edges.map(edge => ({
            ...edge,
            selected: false,
          })),
        },
        metadata: {
          author: 'Current User',
          version: '1.0.0',
          created: new Date().toISOString(),
          nodeCount: workflowData.nodes.length,
          edgeCount: workflowData.edges.length,
        }
      };

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add auth header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/workflows/save`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to save workflow to database:', error);
      throw error;
    }
  }

  /**
   * Update existing workflow in database
   */
  async updateWorkflowInDatabase(workflowId: string, workflowData: Partial<WorkflowSaveRequest>): Promise<WorkflowSaveResponse> {
    try {
      const token = useAuthStore.getState().token;
      
      const payload = {
        ...workflowData,
        template_data: workflowData.nodes && workflowData.edges ? {
          nodes: workflowData.nodes.map(node => ({
            ...node,
            selected: false,
            dragging: false,
          })),
          edges: workflowData.edges.map(edge => ({
            ...edge,
            selected: false,
          })),
        } : undefined,
        metadata: {
          version: '1.0.0',
          updated: new Date().toISOString(),
          nodeCount: workflowData.nodes?.length,
          edgeCount: workflowData.edges?.length,
        }
      };

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/workflows/${workflowId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update workflow in database:', error);
      throw error;
    }
  }

  /**
   * Get all workflows from database
   */
  async getWorkflowsFromDatabase(category?: string, limit: number = 50): Promise<WorkflowSaveResponse[]> {
    try {
      const token = useAuthStore.getState().token;
      
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      params.append('limit', limit.toString());
      params.append('template_type', 'workflow');

      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/workflows?${params.toString()}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return result.workflows || [];
    } catch (error) {
      console.error('Failed to get workflows from database:', error);
      throw error;
    }
  }

  /**
   * Delete workflow from database
   */
  async deleteWorkflowFromDatabase(workflowId: string): Promise<void> {
    try {
      const token = useAuthStore.getState().token;
      
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/workflows/${workflowId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to delete workflow from database:', error);
      throw error;
    }
  }

  /**
   * Extract preview steps from nodes for better display
   */
  private extractPreviewSteps(nodes: Node[]): string[] {
    return nodes
      .slice(0, 5)
      .map(node => {
        const label = node.data?.label || 'Unnamed step';
        return typeof label === 'string' ? label : String(label);
      })
      .filter(step => step.trim().length > 0);
  }

  /**
   * Test database connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/templates/test`);
      return response.ok;
    } catch (error) {
      console.error('Database connection test failed:', error);
      return false;
    }
  }
}

export const workflowService = new WorkflowService();