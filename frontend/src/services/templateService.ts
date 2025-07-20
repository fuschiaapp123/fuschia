import { Node, Edge } from '@xyflow/react';

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  estimatedTime: string;
  complexity: 'Simple' | 'Medium' | 'Advanced';
  usageCount: number;
  steps: number;
  tags: string[];
  preview: string[];
  nodes: Node[];
  edges: Edge[];
  metadata?: {
    author?: string;
    version?: string;
    created?: string;
    updated?: string;
    [key: string]: any;
  };
}

export interface TemplateSettings {
  defaultTemplatesFolder: string;
  customTemplatesFolder: string;
  autoSaveEnabled: boolean;
  templateFileExtension: string;
}

class TemplateService {
  private readonly storageKey = 'fuschia-template-settings';
  private readonly templatesKey = 'fuschia-custom-templates';

  // Default template settings
  private defaultSettings: TemplateSettings = {
    defaultTemplatesFolder: './templates/workflows',
    customTemplatesFolder: './templates/custom',
    autoSaveEnabled: true,
    templateFileExtension: '.json',
  };

  /**
   * Get template settings from localStorage
   */
  getTemplateSettings(): TemplateSettings {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        return { ...this.defaultSettings, ...JSON.parse(stored) };
      }
      return this.defaultSettings;
    } catch (error) {
      console.error('Failed to load template settings:', error);
      return this.defaultSettings;
    }
  }

  /**
   * Save template settings to localStorage
   */
  saveTemplateSettings(settings: Partial<TemplateSettings>): void {
    try {
      const current = this.getTemplateSettings();
      const updated = { ...current, ...settings };
      localStorage.setItem(this.storageKey, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save template settings:', error);
    }
  }

  /**
   * Load template from file input
   */
  async loadTemplateFromFile(file: File): Promise<WorkflowTemplate> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          const template = JSON.parse(content) as WorkflowTemplate;
          
          // Validate template structure
          if (!this.validateTemplate(template)) {
            reject(new Error('Invalid template format'));
            return;
          }
          
          resolve(template);
        } catch (error) {
          reject(new Error('Failed to parse template file'));
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  /**
   * Save template to file
   */
  saveTemplateToFile(template: WorkflowTemplate): void {
    const blob = new Blob([JSON.stringify(template, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.name.toLowerCase().replace(/\s+/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Get saved custom templates from localStorage
   */
  getCustomTemplates(): WorkflowTemplate[] {
    try {
      const stored = localStorage.getItem(this.templatesKey);
      if (stored) {
        return JSON.parse(stored);
      }
      return [];
    } catch (error) {
      console.error('Failed to load custom templates:', error);
      return [];
    }
  }

  /**
   * Save custom template to localStorage
   */
  saveCustomTemplate(template: WorkflowTemplate): void {
    try {
      const templates = this.getCustomTemplates();
      const existingIndex = templates.findIndex(t => t.id === template.id);
      
      if (existingIndex >= 0) {
        templates[existingIndex] = template;
      } else {
        templates.push(template);
      }
      
      localStorage.setItem(this.templatesKey, JSON.stringify(templates));
    } catch (error) {
      console.error('Failed to save custom template:', error);
    }
  }

  /**
   * Delete custom template
   */
  deleteCustomTemplate(templateId: string): void {
    try {
      const templates = this.getCustomTemplates();
      const filtered = templates.filter(t => t.id !== templateId);
      localStorage.setItem(this.templatesKey, JSON.stringify(filtered));
    } catch (error) {
      console.error('Failed to delete custom template:', error);
    }
  }

  /**
   * Convert workflow data to template
   */
  createTemplateFromWorkflow(
    name: string,
    description: string,
    category: string,
    nodes: Node[],
    edges: Edge[]
  ): WorkflowTemplate {
    const template: WorkflowTemplate = {
      id: `custom-${Date.now()}`,
      name,
      description,
      category,
      estimatedTime: 'Variable',
      complexity: 'Medium',
      usageCount: 0,
      steps: nodes.length,
      tags: [category, 'Custom'],
      preview: nodes.slice(0, 5).map(node => String(node.data?.label || 'Unnamed step')),
      nodes: nodes.map(node => ({
        ...node,
        selected: false,
        dragging: false,
      })),
      edges: edges.map(edge => ({
        ...edge,
        selected: false,
      })),
      metadata: {
        author: 'Current User',
        version: '1.0.0',
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
      },
    };

    return template;
  }

  /**
   * Validate template structure
   */
  private validateTemplate(template: any): template is WorkflowTemplate {
    return (
      template &&
      typeof template.id === 'string' &&
      typeof template.name === 'string' &&
      typeof template.description === 'string' &&
      Array.isArray(template.nodes) &&
      Array.isArray(template.edges)
    );
  }

  /**
   * Get built-in templates with actual workflow data
   */
  getBuiltInTemplates(): WorkflowTemplate[] {
    return [
      {
        id: 'employee-onboarding',
        name: 'Employee Onboarding',
        description: 'Automate the complete employee onboarding process from form submission to IT setup',
        category: 'HR',
        estimatedTime: '2-3 hours',
        complexity: 'Medium',
        usageCount: 234,
        steps: 5,
        tags: ['HR', 'Onboarding', 'IT Setup'],
        preview: [
          'New hire form submitted',
          'Create user accounts',
          'Send welcome email',
          'Assign equipment',
          'Schedule orientation'
        ],
        nodes: [
          {
            id: '1',
            type: 'workflowStep',
            position: { x: 100, y: 100 },
            data: {
              label: 'New Hire Form Submitted',
              type: 'trigger',
              description: 'Triggers when new employee form is submitted',
              objective: 'Capture new hire information and initiate onboarding',
              completionCriteria: 'Form data validated and stored',
            },
          },
          {
            id: '2',
            type: 'workflowStep',
            position: { x: 100, y: 250 },
            data: {
              label: 'Create IT Accounts',
              type: 'action',
              description: 'Create email, system accounts, and access permissions',
              objective: 'Provision all necessary IT resources for new employee',
              completionCriteria: 'All accounts created and access granted',
            },
          },
          {
            id: '3',
            type: 'workflowStep',
            position: { x: 100, y: 400 },
            data: {
              label: 'Send Welcome Email',
              type: 'action',
              description: 'Send welcome email with first day information',
              objective: 'Provide new hire with essential first day details',
              completionCriteria: 'Welcome email delivered and confirmed read',
            },
          },
          {
            id: '4',
            type: 'workflowStep',
            position: { x: 300, y: 250 },
            data: {
              label: 'Assign Equipment',
              type: 'action',
              description: 'Reserve and assign laptop, phone, and other equipment',
              objective: 'Ensure new hire has all necessary equipment',
              completionCriteria: 'Equipment assigned and ready for pickup',
            },
          },
          {
            id: '5',
            type: 'workflowStep',
            position: { x: 200, y: 550 },
            data: {
              label: 'Onboarding Complete',
              type: 'end',
              description: 'Mark onboarding process as complete',
              objective: 'Finalize onboarding and notify stakeholders',
              completionCriteria: 'All tasks completed and documented',
            },
          }
        ],
        edges: [
          { id: 'e1-2', source: '1', target: '2', type: 'smoothstep' },
          { id: 'e1-4', source: '1', target: '4', type: 'smoothstep' },
          { id: 'e2-3', source: '2', target: '3', type: 'smoothstep' },
          { id: 'e3-5', source: '3', target: '5', type: 'smoothstep' },
          { id: 'e4-5', source: '4', target: '5', type: 'smoothstep' },
        ],
      },
      {
        id: 'incident-management',
        name: 'IT Incident Management',
        description: 'Automated IT incident triage and resolution workflow with escalation rules',
        category: 'IT Operations',
        estimatedTime: '30 minutes',
        complexity: 'Advanced',
        usageCount: 456,
        steps: 6,
        tags: ['IT', 'Support', 'Escalation'],
        preview: [
          'Incident reported',
          'Auto-classify severity',
          'Assign to team',
          'Send notifications',
          'Track resolution'
        ],
        nodes: [
          {
            id: '1',
            type: 'workflowStep',
            position: { x: 100, y: 100 },
            data: {
              label: 'Incident Reported',
              type: 'trigger',
              description: 'Incident ticket created in support system',
              objective: 'Capture incident details and begin triage process',
              completionCriteria: 'Incident logged with all required information',
            },
          },
          {
            id: '2',
            type: 'workflowStep',
            position: { x: 100, y: 250 },
            data: {
              label: 'Classify Severity',
              type: 'condition',
              description: 'Automatically determine incident severity level',
              objective: 'Classify incident priority for proper routing',
              completionCriteria: 'Severity level assigned (P1, P2, P3, P4)',
            },
          },
          {
            id: '3',
            type: 'workflowStep',
            position: { x: 300, y: 200 },
            data: {
              label: 'Assign to L1 Support',
              type: 'action',
              description: 'Route to Level 1 support team',
              objective: 'Assign to appropriate support team based on severity',
              completionCriteria: 'Ticket assigned and support team notified',
            },
          },
          {
            id: '4',
            type: 'workflowStep',
            position: { x: 300, y: 350 },
            data: {
              label: 'Escalate to L2',
              type: 'condition',
              description: 'Escalate if SLA breach risk or complexity',
              objective: 'Prevent SLA breaches through timely escalation',
              completionCriteria: 'Escalation criteria evaluated and acted upon',
            },
          },
          {
            id: '5',
            type: 'workflowStep',
            position: { x: 500, y: 250 },
            data: {
              label: 'Send Notifications',
              type: 'action',
              description: 'Notify stakeholders of incident status',
              objective: 'Keep relevant parties informed of incident progress',
              completionCriteria: 'All notifications sent and delivered',
            },
          },
          {
            id: '6',
            type: 'workflowStep',
            position: { x: 400, y: 500 },
            data: {
              label: 'Incident Resolved',
              type: 'end',
              description: 'Mark incident as resolved and close ticket',
              objective: 'Close incident and update knowledge base',
              completionCriteria: 'Resolution documented and ticket closed',
            },
          }
        ],
        edges: [
          { id: 'e1-2', source: '1', target: '2', type: 'smoothstep' },
          { id: 'e2-3', source: '2', target: '3', type: 'smoothstep' },
          { id: 'e3-4', source: '3', target: '4', type: 'smoothstep' },
          { id: 'e3-5', source: '3', target: '5', type: 'smoothstep' },
          { id: 'e4-5', source: '4', target: '5', type: 'smoothstep' },
          { id: 'e5-6', source: '5', target: '6', type: 'smoothstep' },
        ],
      },
      {
        id: 'finance-invoice-processing',
        name: 'Invoice Processing',
        description: 'Automate invoice approval and payment processing workflow',
        category: 'Finance',
        estimatedTime: '30-45 minutes',
        complexity: 'Medium',
        usageCount: 89,
        steps: 4,
        tags: ['Finance', 'Invoice', 'Approval'],
        preview: [
          'Invoice received',
          'Validate invoice details',
          'Route for approval',
          'Process payment'
        ],
        nodes: [
          {
            id: '1',
            type: 'workflowStep',
            position: { x: 100, y: 100 },
            data: {
              label: 'Invoice Received',
              type: 'trigger',
              description: 'New invoice submitted for processing',
              objective: 'Capture invoice data and initiate processing',
              completionCriteria: 'Invoice data extracted and validated',
            },
          },
          {
            id: '2',
            type: 'workflowStep',
            position: { x: 100, y: 250 },
            data: {
              label: 'Approval Workflow',
              type: 'condition',
              description: 'Route invoice through approval hierarchy',
              objective: 'Get required approvals based on amount and type',
              completionCriteria: 'Invoice approved or rejected with comments',
            },
          },
          {
            id: '3',
            type: 'workflowStep',
            position: { x: 100, y: 400 },
            data: {
              label: 'Process Payment',
              type: 'action',
              description: 'Execute payment and update systems',
              objective: 'Complete payment process and record transaction',
              completionCriteria: 'Payment processed and recorded',
            },
          }
        ],
        edges: [
          { id: 'e1-2', source: '1', target: '2', type: 'smoothstep' },
          { id: 'e2-3', source: '2', target: '3', type: 'smoothstep' },
        ],
      },
      {
        id: 'sales-lead-qualification',
        name: 'Sales Lead Qualification',
        description: 'Qualify and nurture sales leads through automated workflow',
        category: 'Sales',
        estimatedTime: '15-30 minutes',
        complexity: 'Simple',
        usageCount: 156,
        steps: 3,
        tags: ['Sales', 'Lead', 'Qualification'],
        preview: [
          'Lead captured',
          'Score and qualify',
          'Assign to sales rep'
        ],
        nodes: [
          {
            id: '1',
            type: 'workflowStep',
            position: { x: 100, y: 100 },
            data: {
              label: 'Lead Captured',
              type: 'trigger',
              description: 'New lead information received',
              objective: 'Capture lead data from various sources',
              completionCriteria: 'Lead data stored and initial scoring applied',
            },
          },
          {
            id: '2',
            type: 'workflowStep',
            position: { x: 100, y: 250 },
            data: {
              label: 'Qualify Lead',
              type: 'condition',
              description: 'Score lead based on criteria',
              objective: 'Determine lead quality and potential',
              completionCriteria: 'Lead scored and qualification status determined',
            },
          },
          {
            id: '3',
            type: 'workflowStep',
            position: { x: 100, y: 400 },
            data: {
              label: 'Assign to Sales Rep',
              type: 'action',
              description: 'Route qualified lead to appropriate sales representative',
              objective: 'Connect qualified lead with sales team',
              completionCriteria: 'Lead assigned and sales rep notified',
            },
          }
        ],
        edges: [
          { id: 'e1-2', source: '1', target: '2', type: 'smoothstep' },
          { id: 'e2-3', source: '2', target: '3', type: 'smoothstep' },
        ],
      },
      {
        id: 'compliance-audit-workflow',
        name: 'Compliance Audit',
        description: 'Automated compliance audit and reporting workflow',
        category: 'Compliance',
        estimatedTime: '1-2 hours',
        complexity: 'Advanced',
        usageCount: 34,
        steps: 6,
        tags: ['Compliance', 'Audit', 'Reporting'],
        preview: [
          'Audit initiated',
          'Collect evidence',
          'Review findings',
          'Generate report',
          'Management approval',
          'Submit to authorities'
        ],
        nodes: [
          {
            id: '1',
            type: 'workflowStep',
            position: { x: 100, y: 100 },
            data: {
              label: 'Initiate Audit',
              type: 'trigger',
              description: 'Start compliance audit process',
              objective: 'Begin systematic compliance review',
              completionCriteria: 'Audit scope defined and team assigned',
            },
          },
          {
            id: '2',
            type: 'workflowStep',
            position: { x: 100, y: 250 },
            data: {
              label: 'Evidence Collection',
              type: 'action',
              description: 'Gather compliance evidence and documentation',
              objective: 'Collect all relevant compliance data',
              completionCriteria: 'Evidence collected and organized',
            },
          },
          {
            id: '3',
            type: 'workflowStep',
            position: { x: 100, y: 400 },
            data: {
              label: 'Generate Report',
              type: 'action',
              description: 'Create compliance audit report',
              objective: 'Document findings and recommendations',
              completionCriteria: 'Report generated and reviewed',
            },
          }
        ],
        edges: [
          { id: 'e1-2', source: '1', target: '2', type: 'smoothstep' },
          { id: 'e2-3', source: '2', target: '3', type: 'smoothstep' },
        ],
      }
    ];
  }

  /**
   * Get all templates (built-in + custom)
   */
  getAllTemplates(): WorkflowTemplate[] {
    return [...this.getBuiltInTemplates(), ...this.getCustomTemplates()];
  }

  /**
   * Get all available categories
   */
  getAvailableCategories(): string[] {
    const templates = this.getAllTemplates();
    const categories = new Set(templates.map(t => t.category));
    return Array.from(categories).sort();
  }
}

export const templateService = new TemplateService();