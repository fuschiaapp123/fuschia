import { userService } from './userService';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface WorkflowExecution {
  id: string;
  workflow_template_id: string;
  workflow_name: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  current_tasks: any[];
  completed_tasks: any[];
  failed_tasks: any[];
  started_at: string;
  estimated_completion?: string;
  actual_completion?: string;
  initiated_by: string;
  initiated_by_name: string;
}

export interface AgentOrganization {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'running' | 'paused';
  agents_data: any[];
  connections_data: any[];
  usage_count: number;
  created_by: string;
  created_by_name: string;
  last_activity?: string;
}

class MonitoringService {
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth-storage');
    if (token) {
      try {
        const parsed = JSON.parse(token);
        return {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${parsed.state.token}`,
        };
      } catch (e) {
        console.error('Failed to parse auth token:', e);
      }
    }
    return {
      'Content-Type': 'application/json',
    };
  }

  async getWorkflowExecutions(filterByUser = false): Promise<WorkflowExecution[]> {
    try {
      const url = filterByUser 
        ? `${API_BASE_URL}/monitoring/workflow-executions/me`
        : `${API_BASE_URL}/monitoring/workflow-executions`;
        
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch workflow executions: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching workflow executions:', error);
      // Return mock data for now
      return this.getMockWorkflowExecutions();
    }
  }

  async getAgentOrganizations(filterByUser = false): Promise<AgentOrganization[]> {
    try {
      const url = filterByUser 
        ? `${API_BASE_URL}/monitoring/agent-organizations/me`
        : `${API_BASE_URL}/monitoring/agent-organizations`;
        
      const response = await fetch(url, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch agent organizations: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching agent organizations:', error);
      // Return mock data for now
      return this.getMockAgentOrganizations();
    }
  }

  async getWorkflowExecutionById(executionId: string): Promise<WorkflowExecution | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/workflow-executions/${executionId}`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch workflow execution: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching workflow execution:', error);
      return null;
    }
  }

  async getAgentOrganizationById(organizationId: string): Promise<AgentOrganization | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/monitoring/agent-organizations/${organizationId}`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch agent organization: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching agent organization:', error);
      return null;
    }
  }

  // Mock data methods (for development)
  private getMockWorkflowExecutions(): WorkflowExecution[] {
    const currentUser = this.getCurrentUserFromStorage();
    return [
      {
        id: '1',
        workflow_template_id: 'wf-1',
        workflow_name: 'Customer Onboarding Process',
        status: 'running',
        current_tasks: [
          { id: 'task-2', name: 'KYC Verification', status: 'in_progress' },
          { id: 'task-3', name: 'Document Review', status: 'pending' }
        ],
        completed_tasks: [
          { id: 'task-1', name: 'Initial Application', status: 'completed' }
        ],
        failed_tasks: [],
        started_at: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
        initiated_by: currentUser?.id || 'user-1',
        initiated_by_name: currentUser?.full_name || 'John Doe',
      },
      {
        id: '2',
        workflow_template_id: 'wf-2',
        workflow_name: 'Invoice Processing Workflow',
        status: 'completed',
        current_tasks: [],
        completed_tasks: [
          { id: 'task-4', name: 'OCR Data Extraction', status: 'completed' },
          { id: 'task-5', name: 'Data Validation', status: 'completed' },
          { id: 'task-6', name: 'Approval Routing', status: 'completed' },
          { id: 'task-7', name: 'Payment Processing', status: 'completed' }
        ],
        failed_tasks: [],
        started_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        actual_completion: new Date(Date.now() - 600000).toISOString(), // 10 min ago
        initiated_by: 'user-2',
        initiated_by_name: 'Jane Smith',
      },
      {
        id: '3',
        workflow_template_id: 'wf-3',
        workflow_name: 'Incident Response Protocol',
        status: 'paused',
        current_tasks: [
          { id: 'task-8', name: 'Escalation Review', status: 'pending' }
        ],
        completed_tasks: [
          { id: 'task-9', name: 'Initial Assessment', status: 'completed' },
          { id: 'task-10', name: 'Impact Analysis', status: 'completed' }
        ],
        failed_tasks: [],
        started_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        initiated_by: currentUser?.id || 'user-1',
        initiated_by_name: currentUser?.full_name || 'John Doe',
      },
    ];
  }

  private getMockAgentOrganizations(): AgentOrganization[] {
    const currentUser = this.getCurrentUserFromStorage();
    return [
      {
        id: '1',
        name: 'Customer Service Bot Network',
        description: 'Multi-agent system for automated customer support',
        status: 'running',
        agents_data: [
          { id: 'agent-1', name: 'Intake Agent', status: 'active', role: 'coordinator', type: 'supervisor' },
          { id: 'agent-2', name: 'Classification Agent', status: 'busy', role: 'classifier', type: 'specialist' },
          { id: 'agent-3', name: 'Response Agent', status: 'idle', role: 'responder', type: 'specialist' },
          { id: 'agent-4', name: 'Escalation Agent', status: 'active', role: 'escalator', type: 'executor' }
        ],
        connections_data: [
          { id: 'conn-1', from_agent_id: 'agent-1', to_agent_id: 'agent-2', type: 'control_flow', status: 'active' },
          { id: 'conn-2', from_agent_id: 'agent-2', to_agent_id: 'agent-3', type: 'data_flow', status: 'active' },
          { id: 'conn-3', from_agent_id: 'agent-3', to_agent_id: 'agent-4', type: 'data_flow', status: 'inactive' },
          { id: 'conn-4', from_agent_id: 'agent-4', to_agent_id: 'agent-1', type: 'feedback', status: 'active' }
        ],
        usage_count: 142,
        created_by: currentUser?.id || 'user-1',
        created_by_name: currentUser?.full_name || 'John Doe',
        last_activity: new Date(Date.now() - 300000).toISOString(), // 5 min ago
      },
      {
        id: '2',
        name: 'Document Processing Pipeline',
        description: 'Automated document analysis and intelligent routing',
        status: 'active',
        agents_data: [
          { id: 'agent-5', name: 'OCR Agent', status: 'active', role: 'extractor', type: 'specialist' },
          { id: 'agent-6', name: 'Document Classifier', status: 'idle', role: 'classifier', type: 'specialist' },
          { id: 'agent-7', name: 'Data Validator', status: 'busy', role: 'validator', type: 'specialist' }
        ],
        connections_data: [
          { id: 'conn-5', from_agent_id: 'agent-5', to_agent_id: 'agent-6', type: 'data_flow', status: 'active' },
          { id: 'conn-6', from_agent_id: 'agent-6', to_agent_id: 'agent-7', type: 'data_flow', status: 'active' }
        ],
        usage_count: 89,
        created_by: 'user-2',
        created_by_name: 'Jane Smith',
        last_activity: new Date(Date.now() - 900000).toISOString(), // 15 min ago
      },
      {
        id: '3',
        name: 'Quality Assurance Network',
        description: 'Multi-layered quality control and testing automation',
        status: 'paused',
        agents_data: [
          { id: 'agent-8', name: 'Test Coordinator', status: 'offline', role: 'coordinator', type: 'supervisor' },
          { id: 'agent-9', name: 'Automated Tester', status: 'idle', role: 'tester', type: 'specialist' },
          { id: 'agent-10', name: 'Report Generator', status: 'idle', role: 'reporter', type: 'executor' }
        ],
        connections_data: [
          { id: 'conn-7', from_agent_id: 'agent-8', to_agent_id: 'agent-9', type: 'control_flow', status: 'inactive' },
          { id: 'conn-8', from_agent_id: 'agent-9', to_agent_id: 'agent-10', type: 'data_flow', status: 'inactive' }
        ],
        usage_count: 34,
        created_by: currentUser?.id || 'user-1',
        created_by_name: currentUser?.full_name || 'John Doe',
        last_activity: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
      },
    ];
  }

  private getCurrentUserFromStorage() {
    try {
      const authStorage = localStorage.getItem('auth-storage');
      if (authStorage) {
        const parsed = JSON.parse(authStorage);
        return parsed.state.user;
      }
    } catch (e) {
      console.error('Failed to get user from storage:', e);
    }
    return null;
  }
}

export const monitoringService = new MonitoringService();