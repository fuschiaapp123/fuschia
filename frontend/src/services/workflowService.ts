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
  use_memory_enhancement?: boolean;
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
      
      // DEBUG: Log what we're about to send
      console.log('🔍 DEBUG: Preparing to save workflow:');
      console.log('   - use_memory_enhancement from workflowData:', workflowData.use_memory_enhancement);
      
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
        use_memory_enhancement: workflowData.use_memory_enhancement || false,
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

      // DEBUG: Log the complete payload
      console.log('🔍 DEBUG: Complete payload to send:', JSON.stringify(payload, null, 2));
      console.log('🔍 DEBUG: payload.use_memory_enhancement:', payload.use_memory_enhancement);

      // DEBUG: Log node types specifically
      console.log('🔍 DEBUG: Node types being saved:');
      payload.template_data.nodes.forEach((node: any, index: number) => {
        console.log(`   Node ${index + 1}: ${node.data?.label || 'Unnamed'} - Type: ${node.data?.type || 'MISSING'}`);
      });

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add auth header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      alert("Saving workflow to database...");
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
   * Get workflow templates from database formatted for the template loader
   */
  async getWorkflowTemplatesFromDatabase(): Promise<any[]> {
    try {
      const token = useAuthStore.getState().token;
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/workflows`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Details:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Database workflow templates response:', result);
      console.log('Number of workflows returned:', result.workflows?.length || 0);
      if (result.workflows && result.workflows.length > 0) {
        console.log('First workflow sample:', result.workflows[0]);
        console.log('First workflow template_data:', result.workflows[0].template_data);
      }
      
      // Convert database templates to frontend format
      const templates = result.workflows || [];
      return templates.map((template: any) => {
        const convertedTemplate = {
          id: template.id,
          name: template.name || 'Untitled Template',
          description: template.description || 'No description available',
          category: template.category || 'Custom',
          complexity: (template.complexity || 'medium').toLowerCase(),
          estimatedTime: template.estimated_time || 'Variable',
          steps: template.template_data?.nodes?.length || 0,
          usageCount: template.usage_count || 0,
          template_type: 'workflow',
          tags: template.tags || [],
          preview: template.preview_steps || [],
          // Load from the correct workflow template fields
          nodes: template.template_data?.nodes || [],
          edges: template.template_data?.edges || [],
          metadata: template.metadata || {}
        };
        
        // Debug logging only if nodes/edges are empty
        if (!convertedTemplate.nodes.length && !convertedTemplate.edges.length) {
          console.log('Empty template found:', template.name);
          console.log('Template data structure:', template.template_data);
        }
        
        return convertedTemplate;
      });
    } catch (error) {
      console.error('Failed to fetch workflow templates from database:', error);
      throw error;
    }
  }

  /**
   * Test database connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      // Use the workflows/test endpoint for proper connectivity testing
      const response = await fetch(`${this.baseUrl}/workflows/test`);
      return response.ok;
    } catch (error) {
      console.error('Database connection test failed:', error);
      return false;
    }
  }
}

export const workflowService = new WorkflowService();