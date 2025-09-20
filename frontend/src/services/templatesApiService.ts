// API service for fetching templates from the database
import { WorkflowTemplate, AgentTemplate } from './templateService';
import { useAuthStore } from '@/store/authStore';

export interface WorkflowTemplateApiResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  template_type: string;
  complexity: string;
  estimated_time: string;
  usage_count: number;
  status: string;
  created_at: string;
  created_by: string;
  template_data?: any;
  metadata?: any;
  tags?: string[];
  preview_steps?: string[];
  use_memory_enhancement?: boolean;
}

export interface AgentTemplateApiResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  complexity: string;
  estimated_time: string;
  tags: string[];
  usage_count: number;
  status: string;
  created_at: string;
  created_by: string;
  agents_data?: any[];
  connections_data?: any[];
  template_metadata?: any;
}

export interface WorkflowTemplatesApiResponse {
  workflows: WorkflowTemplateApiResponse[];
  total_count: number;
  categories: string[];
}

export interface AgentTemplatesApiResponse {
  templates: AgentTemplateApiResponse[];
  total_count: number;
  categories: string[];
}

class TemplatesApiService {
  private readonly baseUrl = '/api/v1';

  /**
   * Create authenticated headers for API requests
   */
  private createAuthHeaders(): Headers {
    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    
    // Get token from auth store
    const token = useAuthStore.getState().token;
    console.log('🔑 Templates API: Auth token available:', !!token, token ? `${token.substring(0, 20)}...` : 'none');
    
    if (token) {
      headers.append("Authorization", `Bearer ${token}`);
      console.log('✅ Templates API: Added Authorization header to request');
    } else {
      console.warn('⚠️ Templates API: No auth token available - request will be anonymous');
    }
    
    return headers;
  }

  /**
   * Fetch workflow templates from the database
   */
  async fetchWorkflowTemplates(
    limit?: number,
    offset?: number,
    category?: string,
    query?: string
  ): Promise<WorkflowTemplatesApiResponse> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to view templates.');
      }
      const params = new URLSearchParams();
      if (limit) params.append('limit', limit.toString());
      if (offset) params.append('offset', offset.toString());
      if (category) params.append('category', category);
      if (query) params.append('query', query);

      const response = await fetch(`${this.baseUrl}/workflows/?${params.toString()}`, {
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`Failed to fetch workflow templates: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching workflow templates:', error);
      throw error;
    }
  }

  /**
   * Fetch agent templates from the database
   */
  async fetchAgentTemplates(
    limit?: number,
    offset?: number,
    category?: string
  ): Promise<AgentTemplatesApiResponse> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to view templates.');
      }
      const params = new URLSearchParams();
      if (limit) params.append('limit', limit.toString());
      if (offset) params.append('offset', offset.toString());
      if (category) params.append('category', category);

      const response = await fetch(`${this.baseUrl}/agents/templates?${params.toString()}`, {
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`Failed to fetch agent templates: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching agent templates:', error);
      throw error;
    }
  }

  /**
   * Fetch a specific workflow template by ID
   */
  async fetchWorkflowTemplate(id: string): Promise<WorkflowTemplateApiResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/${id}`, {
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch workflow template: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflow template:', error);
      throw error;
    }
  }

  /**
   * Fetch a specific agent template by ID
   */
  async fetchAgentTemplate(id: string): Promise<AgentTemplateApiResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/agents/templates/${id}`, {
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch agent template: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching agent template:', error);
      throw error;
    }
  }

  /**
   * Convert API response to frontend WorkflowTemplate format
   */
  convertApiToWorkflowTemplate(apiTemplate: WorkflowTemplateApiResponse): WorkflowTemplate {
    // Extract nodes and edges from template_data
    const templateData = apiTemplate.template_data || {};
    const nodes = templateData.nodes || [];
    const edges = templateData.edges || [];
    
    return {
      id: apiTemplate.id,
      name: apiTemplate.name,
      description: apiTemplate.description,
      category: apiTemplate.category,
      estimatedTime: apiTemplate.estimated_time,
      complexity: this.normalizeComplexity(apiTemplate.complexity),
      usageCount: apiTemplate.usage_count,
      steps: nodes.length || 0,
      tags: apiTemplate.tags || [],
      preview: apiTemplate.preview_steps || [],
      nodes: nodes,
      edges: edges,
      template_type: 'workflow',
      use_memory_enhancement: apiTemplate.use_memory_enhancement,
      metadata: {
        author: apiTemplate.created_by || 'Unknown',
        created: apiTemplate.created_at,
        ...apiTemplate.metadata
      }
    };
  }

  /**
   * Normalize complexity values to match frontend expectations
   */
  private normalizeComplexity(complexity: string): 'Simple' | 'Medium' | 'Advanced' {
    const normalized = complexity.toLowerCase();
    if (normalized === 'simple') return 'Simple';
    if (normalized === 'medium') return 'Medium';
    if (normalized === 'advanced' || normalized === 'complex') return 'Advanced';
    return 'Medium'; // Default fallback
  }

  /**
   * Normalize tools to array of strings (React-safe)
   * Handles complex tool objects and converts them to simple string representations
   */
  private normalizeTools(tools: any[]): string[] {
    if (!Array.isArray(tools)) return [];
    
    return tools.map(tool => {
      if (typeof tool === 'string') {
        return tool.trim();
      } else if (tool && typeof tool === 'object') {
        // Handle tool objects by extracting the name property
        if (tool.name && typeof tool.name === 'string') {
          return tool.name.trim();
        } else if (tool.tool_name && typeof tool.tool_name === 'string') {
          return tool.tool_name.trim();
        } else if (tool.type && typeof tool.type === 'string') {
          return tool.type.trim();
        } else {
          // Fallback: try to find any string property that could represent the tool name
          const keys = Object.keys(tool);
          for (const key of keys) {
            if (typeof tool[key] === 'string' && tool[key].trim().length > 0) {
              return tool[key].trim();
            }
          }
          return 'Unknown Tool';
        }
      } else if (tool !== null && tool !== undefined) {
        return String(tool).trim();
      } else {
        return '';
      }
    }).filter(tool => tool && tool.length > 0);
  }

  /**
   * Convert API response to frontend AgentTemplate format
   */
  convertApiToAgentTemplate(apiTemplate: AgentTemplateApiResponse): AgentTemplate {
    // Convert agents_data to proper ReactFlow nodes
    const agentsData = apiTemplate.agents_data || [];
    console.log(`🔧 Converting agent template "${apiTemplate.name}":`, {
      agentsDataCount: agentsData.length,
      connectionsDataCount: (apiTemplate.connections_data || []).length,
      sampleAgentData: agentsData[0],
      sampleTools: agentsData[0]?.tools
    });
    const nodes = agentsData.map((agentData, index) => ({
      id: agentData.id || `agent-${index}`,
      type: 'agentNode',
      position: agentData.position || { 
        x: 100 + (index % 3) * 250, 
        y: 100 + Math.floor(index / 3) * 200 
      },
      data: {
        name: agentData.name || `Agent ${index + 1}`,
        role: agentData.role || 'executor',
        skills: Array.isArray(agentData.skills) ? agentData.skills.filter((skill: any) => typeof skill === 'string') : [],
        tools: this.normalizeTools(agentData.tools || []),
        description: agentData.description || '',
        status: agentData.status || 'active',
        level: agentData.level || 1,
        department: agentData.department || 'General',
        maxConcurrentTasks: agentData.maxConcurrentTasks || agentData.max_concurrent_tasks || 5,
        strategy: agentData.strategy || 'simple',
        // Only include safe, primitive properties to avoid React rendering errors
        capabilities: Array.isArray(agentData.capabilities) ? agentData.capabilities.filter((cap: any) => typeof cap === 'string') : [],
        instructions: typeof agentData.instructions === 'string' ? agentData.instructions : '',
        model: typeof agentData.model === 'string' ? agentData.model : '',
        temperature: typeof agentData.temperature === 'number' ? agentData.temperature : 0.7
      }
    }));

    console.log(`🔧 Converted nodes:`, nodes.map(n => ({ id: n.id, tools: n.data.tools, dataKeys: Object.keys(n.data) })));

    // Convert connections_data to proper ReactFlow edges
    const connectionsData = apiTemplate.connections_data || [];
    const edges = connectionsData.map((connection, index) => ({
      id: connection.id || `edge-${index}`,
      source: connection.source || connection.from_agent_id,
      target: connection.target || connection.to_agent_id,
      type: 'smoothstep',
      style: { stroke: '#8b5cf6', strokeWidth: 2 },
      label: connection.label || connection.connection_type || '',
      ...connection
    }));

    return {
      id: apiTemplate.id,
      name: apiTemplate.name,
      description: apiTemplate.description,
      category: apiTemplate.category,
      estimatedTime: apiTemplate.estimated_time,
      complexity: this.normalizeComplexity(apiTemplate.complexity),
      usageCount: apiTemplate.usage_count,
      agentCount: nodes.length,
      features: apiTemplate.template_metadata?.features || [],
      useCase: apiTemplate.template_metadata?.useCase || '',
      tags: apiTemplate.tags || [],
      preview: apiTemplate.template_metadata?.preview || [],
      nodes: nodes,
      edges: edges,
      template_type: 'agent',
      metadata: {
        author: apiTemplate.created_by || 'Unknown',
        created: apiTemplate.created_at,
        ...apiTemplate.template_metadata
      }
    };
  }

  /**
   * Delete a workflow template
   */
  async deleteWorkflowTemplate(id: string): Promise<{ status: string; message: string; workflow_id: string }> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to delete templates.');
      }

      const response = await fetch(`${this.baseUrl}/workflows/${id}`, {
        method: 'DELETE',
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Not authorized to delete this template.');
        }
        if (response.status === 404) {
          throw new Error('Template not found.');
        }
        throw new Error(`Failed to delete workflow template: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error deleting workflow template:', error);
      throw error;
    }
  }

  /**
   * Clone a workflow template by creating a new one with copied data
   */
  async cloneWorkflowTemplate(originalTemplate: WorkflowTemplateApiResponse): Promise<WorkflowTemplateApiResponse> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to clone templates.');
      }

      // Create the cloned template data
      const cloneData = {
        name: `${originalTemplate.name} (Copy)`,
        description: `Copy of ${originalTemplate.description}`,
        category: originalTemplate.category,
        template_type: originalTemplate.template_type,
        complexity: originalTemplate.complexity,
        estimated_time: originalTemplate.estimated_time,
        tags: [...(originalTemplate.tags || []), 'Cloned'],
        preview_steps: originalTemplate.preview_steps || [],
        template_data: originalTemplate.template_data || {},
        metadata: {
          ...(originalTemplate.metadata || {}),
          cloned_from: originalTemplate.id,
          cloned_at: new Date().toISOString()
        },
        use_memory_enhancement: originalTemplate.use_memory_enhancement || false
      };

      const response = await fetch(`${this.baseUrl}/workflows/save`, {
        method: 'POST',
        headers: this.createAuthHeaders(),
        body: JSON.stringify(cloneData)
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Not authorized to clone templates.');
        }
        throw new Error(`Failed to clone workflow template: ${response.status} ${response.statusText}`);
      }

      const clonedTemplate = await response.json();
      return clonedTemplate;
    } catch (error) {
      console.error('Error cloning workflow template:', error);
      throw error;
    }
  }

  /**
   * Clone an agent template by creating a new one with copied data
   */
  async cloneAgentTemplate(originalTemplate: AgentTemplateApiResponse): Promise<AgentTemplateApiResponse> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to clone templates.');
      }

      // Create the cloned template data matching agents endpoint format
      const cloneData = {
        name: `${originalTemplate.name} (Copy)`,
        description: `Copy of ${originalTemplate.description}`,
        category: originalTemplate.category,
        complexity: originalTemplate.complexity,
        estimated_time: originalTemplate.estimated_time,
        tags: [...(originalTemplate.tags || []), 'Cloned'],
        preview_steps: [], // Agent templates don't typically have preview steps
        // Direct fields expected by agents endpoint
        agents_data: originalTemplate.agents_data || [],
        connections_data: originalTemplate.connections_data || [],
        template_metadata: {
          ...(originalTemplate.template_metadata || {}),
          cloned_from: originalTemplate.id,
          cloned_at: new Date().toISOString()
        }
      };

      // Use the agents templates endpoint specifically for agent templates
      const response = await fetch(`${this.baseUrl}/agents/templates`, {
        method: 'POST',
        headers: this.createAuthHeaders(),
        body: JSON.stringify(cloneData)
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Not authorized to clone templates.');
        }
        throw new Error(`Failed to clone agent template: ${response.status} ${response.statusText}`);
      }

      const clonedTemplate = await response.json();
      
      // The agents endpoint returns data directly - convert to match AgentTemplateApiResponse format
      return {
        id: clonedTemplate.id,
        name: clonedTemplate.name,
        description: clonedTemplate.description,
        category: clonedTemplate.category,
        complexity: clonedTemplate.complexity,
        estimated_time: clonedTemplate.estimated_time,
        tags: clonedTemplate.tags || [],
        usage_count: clonedTemplate.usage_count || 0,
        status: clonedTemplate.status,
        created_at: clonedTemplate.created_at,
        created_by: clonedTemplate.created_by,
        // The agents endpoint returns these fields directly
        agents_data: clonedTemplate.agents_data || [],
        connections_data: clonedTemplate.connections_data || [],
        template_metadata: clonedTemplate.template_metadata || {}
      };
    } catch (error) {
      console.error('Error cloning agent template:', error);
      throw error;
    }
  }

  /**
   * Delete an agent template
   */
  async deleteAgentTemplate(id: string): Promise<{ status: string; message: string; template_id: string }> {
    try {
      // Check if user is authenticated first
      const token = useAuthStore.getState().token;
      if (!token) {
        throw new Error('Authentication required. Please log in to delete templates.');
      }

      const response = await fetch(`${this.baseUrl}/agents/templates/${id}`, {
        method: 'DELETE',
        headers: this.createAuthHeaders()
      });
      
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Not authorized to delete this template.');
        }
        if (response.status === 404) {
          throw new Error('Template not found.');
        }
        throw new Error(`Failed to delete agent template: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error deleting agent template:', error);
      throw error;
    }
  }
}

export const templatesApiService = new TemplatesApiService();