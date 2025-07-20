import React from 'react';
import { cn } from '@/utils/cn';
import { Play, Copy, Download, Clock, Users, CheckCircle } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { templateService } from '@/services/templateService';

interface WorkflowTemplate {
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
}

const workflowTemplates: WorkflowTemplate[] = [
  {
    id: '1',
    name: 'Employee Onboarding',
    description: 'Automate the complete employee onboarding process from form submission to IT setup',
    category: 'HR',
    estimatedTime: '2-3 hours',
    complexity: 'Medium',
    usageCount: 234,
    steps: 8,
    tags: ['HR', 'Onboarding', 'IT Setup'],
    preview: [
      'New hire form submitted',
      'Create user accounts',
      'Send welcome email',
      'Assign equipment',
      'Schedule orientation'
    ]
  },
  {
    id: '2',
    name: 'Incident Management',
    description: 'Automated IT incident triage and resolution workflow with escalation rules',
    category: 'IT Operations',
    estimatedTime: '30 minutes',
    complexity: 'Advanced',
    usageCount: 456,
    steps: 12,
    tags: ['IT', 'Support', 'Escalation'],
    preview: [
      'Incident reported',
      'Auto-classify severity',
      'Assign to team',
      'Send notifications',
      'Track resolution'
    ]
  },
  {
    id: '3',
    name: 'Invoice Processing',
    description: 'Streamline invoice approval and payment processing workflow',
    category: 'Finance',
    estimatedTime: '1 hour',
    complexity: 'Simple',
    usageCount: 189,
    steps: 6,
    tags: ['Finance', 'Approval', 'Payment'],
    preview: [
      'Invoice received',
      'Extract data',
      'Route for approval',
      'Process payment',
      'Update records'
    ]
  },
  {
    id: '4',
    name: 'Lead Qualification',
    description: 'Automatically qualify and route sales leads based on scoring criteria',
    category: 'Sales',
    estimatedTime: '45 minutes',
    complexity: 'Medium',
    usageCount: 312,
    steps: 7,
    tags: ['Sales', 'CRM', 'Scoring'],
    preview: [
      'Lead captured',
      'Score lead quality',
      'Route to sales rep',
      'Send follow-up',
      'Track progress'
    ]
  },
  {
    id: '5',
    name: 'Content Approval',
    description: 'Multi-stage content review and approval workflow for marketing materials',
    category: 'Marketing',
    estimatedTime: '1-2 hours',
    complexity: 'Simple',
    usageCount: 98,
    steps: 5,
    tags: ['Marketing', 'Approval', 'Content'],
    preview: [
      'Content submitted',
      'Review assignment',
      'Collect feedback',
      'Make revisions',
      'Final approval'
    ]
  },
  {
    id: '6',
    name: 'Customer Escalation',
    description: 'Automated customer support escalation based on priority and SLA rules',
    category: 'Customer Support',
    estimatedTime: '20 minutes',
    complexity: 'Advanced',
    usageCount: 167,
    steps: 9,
    tags: ['Support', 'SLA', 'Escalation'],
    preview: [
      'Support ticket created',
      'Check SLA status',
      'Auto-escalate if needed',
      'Notify managers',
      'Track resolution time'
    ]
  }
];

const getComplexityColor = (complexity: string) => {
  switch (complexity) {
    case 'Simple':
      return 'bg-green-100 text-green-800';
    case 'Medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'Advanced':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

interface WorkflowTemplateCardProps {
  template: WorkflowTemplate;
  onUse: (template: WorkflowTemplate) => void;
  onClone: (template: WorkflowTemplate) => void;
}

const WorkflowTemplateCard: React.FC<WorkflowTemplateCardProps> = ({ template, onUse, onClone }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{template.name}</h3>
          <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
            {template.category}
          </span>
        </div>
        <span className={cn(
          'inline-block px-2 py-1 text-xs font-medium rounded-full',
          getComplexityColor(template.complexity)
        )}>
          {template.complexity}
        </span>
      </div>
      
      <p className="text-gray-600 text-sm mb-4 leading-relaxed">
        {template.description}
      </p>
      
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>{template.estimatedTime}</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="w-4 h-4" />
              <span>{template.steps} steps</span>
            </div>
            <div className="flex items-center space-x-1">
              <Users className="w-4 h-4" />
              <span>{template.usageCount} uses</span>
            </div>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1">
          {template.tags.map((tag) => (
            <span
              key={tag}
              className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
      
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Preview Steps:</h4>
        <ul className="space-y-1">
          {template.preview.slice(0, 3).map((step, index) => (
            <li key={index} className="text-xs text-gray-600 flex items-center space-x-2">
              <span className="w-4 h-4 bg-gray-200 rounded-full flex items-center justify-center text-xs">
                {index + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
          {template.preview.length > 3 && (
            <li className="text-xs text-gray-400 ml-6">
              +{template.preview.length - 3} more steps...
            </li>
          )}
        </ul>
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={() => onUse(template)}
          className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
        >
          <Play className="w-4 h-4" />
          <span>Use Template</span>
        </button>
        <button
          onClick={() => onClone(template)}
          className="flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
        >
          <Copy className="w-4 h-4" />
        </button>
        <button className="flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
          <Download className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const WorkflowTemplates: React.FC = () => {
  const { setActiveTab, setWorkflowData } = useAppStore();

  const handleUseTemplate = (template: WorkflowTemplate) => {
    // Find the full template data from the service
    const fullTemplate = templateService.getAllTemplates().find(t => t.name === template.name);
    if (fullTemplate) {
      // Set the workflow data in the app store
      setWorkflowData({
        nodes: fullTemplate.nodes,
        edges: fullTemplate.edges,
      });
      
      // Switch to the designer tab
      setActiveTab('designer');
    } else {
      alert('Template data not found. Please try again.');
    }
  };

  const handleCloneTemplate = (template: WorkflowTemplate) => {
    const fullTemplate = templateService.getAllTemplates().find(t => t.name === template.name);
    if (fullTemplate) {
      // Create a copy with a new ID and name
      const clonedTemplate = templateService.createTemplateFromWorkflow(
        `${template.name} (Copy)`,
        `Copy of ${template.description}`,
        template.category,
        fullTemplate.nodes,
        fullTemplate.edges
      );
      
      // Save the cloned template
      templateService.saveCustomTemplate(clonedTemplate);
      alert('Template cloned successfully!');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow Templates</h2>
        <p className="text-gray-600">
          Get started quickly with pre-built workflow templates for common business processes
        </p>
      </div>
      
      <div className="mb-6">
        <div className="flex items-center space-x-4">
          <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
            <option>All Categories</option>
            <option>HR</option>
            <option>IT Operations</option>
            <option>Finance</option>
            <option>Sales</option>
            <option>Marketing</option>
            <option>Customer Support</option>
          </select>
          
          <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
            <option>All Complexity</option>
            <option>Simple</option>
            <option>Medium</option>
            <option>Advanced</option>
          </select>
          
          <div className="flex-1" />
          
          <span className="text-sm text-gray-500">
            {workflowTemplates.length} templates available
          </span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workflowTemplates.map((template) => (
          <WorkflowTemplateCard
            key={template.id}
            template={template}
            onUse={handleUseTemplate}
            onClone={handleCloneTemplate}
          />
        ))}
      </div>
    </div>
  );
};