import { api } from '@/utils/api';
import { AgentData, AgentTool } from '@/components/agents/AgentDesigner';

export interface AgentOrganizationCreate {
  name: string;
  description: string;
  version?: string;
  agents: AgentNode[];
  connections: AgentConnection[];
  entry_points: string[];
  max_execution_time_minutes?: number;
  require_human_supervision?: boolean;
  allow_parallel_execution?: boolean;
  tags?: string[];
  use_cases?: string[];
}

export interface AgentNode {
  id: string;
  name: string;
  role: 'coordinator' | 'specialist' | 'validator' | 'human_liaison' | 'tool_executor';
  strategy: 'chain_of_thought' | 'react' | 'hybrid';
  capabilities: AgentCapability[];
  tools: AgentTool[];
  max_iterations?: number;
  confidence_threshold?: number;
  requires_human_approval?: boolean;
  human_escalation_threshold?: number;
  approval_timeout_seconds?: number;
  can_handoff_to?: string[];
  accepts_handoffs_from?: string[];
  handoff_criteria?: Record<string, any>;
  response_timeout_seconds?: number;
  max_concurrent_tasks?: number;
  priority_level?: number;
}

export interface AgentCapability {
  name: string;
  description: string;
  confidence_level: number;
  tools_required: string[];
}

export interface AgentConnection {
  source_agent_id: string;
  target_agent_id: string;
  connection_type: string;
  conditions?: Record<string, any>;
  weight?: number;
}

class AgentService {
  private baseUrl = 'http://localhost:8000/api/v1';

  /**
   * Convert frontend AgentData to backend AgentNode format
   */
  private convertToAgentNode(agentData: AgentData): AgentNode {
    // Map frontend roles to backend roles
    const roleMapping = {
      'supervisor': 'coordinator',
      'specialist': 'specialist', 
      'coordinator': 'coordinator',
      'executor': 'tool_executor'
    } as const;

    // Create capabilities from skills
    const capabilities: AgentCapability[] = agentData.skills.map(skill => ({
      name: skill,
      description: `Capability for ${skill}`,
      confidence_level: 0.8, // Default confidence
      tools_required: agentData.agentTools?.filter(tool => 
        tool.configuration.custom_skill === skill || 
        tool.name.includes(skill.toLowerCase().replace(/\s+/g, '_'))
      ).map(tool => tool.name) || []
    }));

    return {
      id: `agent_${agentData.name.toLowerCase().replace(/\s+/g, '_')}`,
      name: agentData.name,
      role: roleMapping[agentData.role] || 'tool_executor',
      strategy: 'hybrid', // Default strategy
      capabilities,
      tools: agentData.agentTools || [],
      max_iterations: 10,
      confidence_threshold: 0.8,
      requires_human_approval: false,
      human_escalation_threshold: 0.5,
      approval_timeout_seconds: 300,
      can_handoff_to: [],
      accepts_handoffs_from: [],
      handoff_criteria: {},
      response_timeout_seconds: 30,
      max_concurrent_tasks: agentData.maxConcurrentTasks || 3,
      priority_level: agentData.level + 1
    };
  }

  /**
   * Save agent configuration to backend
   */
  async saveAgent(agentData: AgentData): Promise<string> {
    try {
      const agentNode = this.convertToAgentNode(agentData);
      
      // Create a simple agent organization with just this agent
      const organization: AgentOrganizationCreate = {
        name: `${agentData.name} Organization`,
        description: `Agent organization for ${agentData.name}`,
        version: '1.0.0',
        agents: [agentNode],
        connections: [],
        entry_points: [agentNode.id],
        max_execution_time_minutes: 60,
        require_human_supervision: true,
        allow_parallel_execution: true,
        tags: agentData.skills,
        use_cases: [`${agentData.department} operations`].filter(Boolean)
      };

      const response = await api.post('/agents/organizations', organization);

      return response.data.id;
    } catch (error) {
      console.error('Failed to save agent:', error);
      throw error;
    }
  }

  /**
   * Save agent template to database using the dedicated agents endpoint
   */
  async saveAgentTemplateToDatabase(templateData: {
    id?: string; // Optional ID for updating existing templates
    name: string;
    description: string;
    category: string;
    complexity: 'Simple' | 'Medium' | 'Advanced';
    estimatedTime: string;
    tags: string[];
    agentCount: number;
    features: string[];
    useCase: string;
    nodes: any[];
    edges: any[];
  }): Promise<{ id: string; name: string; created_at: string }> {
    try {
      // Get auth token from store
      const { useAuthStore } = await import('@/store/authStore');
      const token = useAuthStore.getState().token;

      // Prepare payload for agent template endpoint - using agents_data and connections_data
      const payload = {
        id: templateData.id, // Include ID for upsert logic
        name: templateData.name,
        description: templateData.description,
        category: templateData.category,
        complexity: templateData.complexity.toLowerCase(),
        estimated_time: templateData.estimatedTime,
        tags: templateData.tags,
        preview_steps: templateData.nodes.slice(0, 5).map(node => 
          node.data?.name || 'Unnamed Agent'
        ),
        // Store agent data in the correct fields for agent templates
        agents_data: templateData.nodes,
        connections_data: templateData.edges,
        template_metadata: {
          author: 'Current User',
          version: '1.0.0',
          created: new Date().toISOString(),
          agentCount: templateData.agentCount,
          edgeCount: templateData.edges.length,
          features: templateData.features,
          useCase: templateData.useCase,
        }
      };

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add auth header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Use the dedicated agents/templates endpoint
      const response = await fetch(`${this.baseUrl}/agents/templates`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return {
        id: result.id,
        name: result.name,
        created_at: result.created_at
      };
    } catch (error) {
      console.error('Failed to save agent template to database:', error);
      throw error;
    }
  }

  /**
   * Get agent templates from database
   */
  async getAgentTemplatesFromDatabase(): Promise<any[]> {
    try {
      // Get auth token from store
      const { useAuthStore } = await import('@/store/authStore');
      const token = useAuthStore.getState().token;

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add auth header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.baseUrl}/agents/templates`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Details:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log('API Response:', result);
      
      // Convert database templates to frontend format - reading from agents_data and connections_data
      const templates = result.templates || [];
      return templates.map((template: any) => ({
        id: template.id,
        name: template.name || 'Untitled Template',
        description: template.description || 'No description available',
        category: template.category || 'Custom',
        complexity: (template.complexity || 'medium').toLowerCase(),
        estimatedTime: template.estimated_time || 'Variable',
        agentCount: template.agents_data?.length || 0,
        features: this.extractFeaturesFromTemplate(template),
        useCase: template.template_metadata?.useCase || `${template.category || 'Custom'} operations`,
        // Load from the correct agent template fields
        nodes: template.agents_data || [],
        edges: template.connections_data || [],
        tags: template.tags || []
      }));
    } catch (error) {
      console.error('Failed to fetch agent templates from database:', error);
      throw error;
    }
  }

  /**
   * Extract features from template data
   */
  private extractFeaturesFromTemplate(template: any): string[] {
    const features = [];
    
    try {
      // Extract features from template metadata (updated location)
      if (template.template_metadata?.features && Array.isArray(template.template_metadata.features)) {
        features.push(...template.template_metadata.features);
      }
      
      // Extract features from agents_data (agent skills and capabilities)
      if (template.agents_data && Array.isArray(template.agents_data)) {
        template.agents_data.forEach((agent: any) => {
          try {
            // Extract from agent skills (ReactFlow node data)
            if (agent.data?.skills && Array.isArray(agent.data.skills)) {
              agent.data.skills.forEach((skill: string) => {
                if (skill && typeof skill === 'string' && !features.includes(skill)) {
                  features.push(skill);
                }
              });
            }
            
            // Extract from agent capabilities (backend format)
            if (agent.capabilities && Array.isArray(agent.capabilities)) {
              agent.capabilities.forEach((cap: any) => {
                if (cap?.name && typeof cap.name === 'string' && !features.includes(cap.name)) {
                  features.push(cap.name);
                }
              });
            }
          } catch (agentError) {
            console.warn('Error extracting features from agent:', agentError);
          }
        });
      }
    } catch (error) {
      console.warn('Error extracting features from template:', error);
    }
    
    // Default features based on category
    if (features.length === 0) {
      const defaultFeatures: Record<string, string[]> = {
        'customer-service': ['Multi-channel Support', 'Escalation Management', 'Ticket Routing'],
        'data-analytics': ['Data Processing', 'Statistical Analysis', 'Reporting'],
        'security': ['Threat Detection', 'Incident Response', 'Monitoring'],
        'development': ['Code Review', 'Testing', 'Deployment'],
        'enterprise': ['Workflow Management', 'Integration', 'Automation']
      };
      
      features.push(...(defaultFeatures[template.category] || ['General Purpose', 'Multi-Agent', 'Automation']));
    }
    
    return features.slice(0, 5); // Limit to 5 features
  }

  /**
   * Test database connection
   */
  async testConnection(): Promise<boolean> {
    try {
      // Use the agents/test endpoint for proper connectivity testing
      const response = await fetch(`${this.baseUrl}/agents/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Database connection test failed:', error);
      return false;
    }
  }

  /**
   * Get available agent tools from backend
   */
  async getAvailableTools(): Promise<AgentTool[]> {
    try {
      const response = await api.get('/agent-tools');
      
      return response.data.tools || [];
    } catch (error) {
      console.error('Failed to get available tools:', error);
      return [];
    }
  }

  /**
   * Validate agent configuration
   */
  validateAgent(agentData: AgentData): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!agentData.name.trim()) {
      errors.push('Agent name is required');
    }

    // Skills are optional - agents can work with just tools

    if (!agentData.description.trim()) {
      errors.push('Agent description is required');
    }

    if (agentData.maxConcurrentTasks && agentData.maxConcurrentTasks < 1) {
      errors.push('Max concurrent tasks must be at least 1');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export const agentService = new AgentService();