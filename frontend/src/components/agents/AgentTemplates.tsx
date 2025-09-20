import React, { useState, useEffect } from 'react';
import { Node, Edge } from '@xyflow/react';
import { 
  Users, 
  Building2, 
  Brain, 
  Workflow, 
  Database, 
  MessageSquare, 
  Shield, 
  Zap,
  Download,
  Play,
  Copy,
  Star,
  Loader,
  Trash2
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAppStore } from '@/store/appStore';
import { AgentData } from './AgentDesigner';
import { templateService, AgentTemplate } from '@/services/templateService';
import { templatesApiService } from '@/services/templatesApiService';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

// AgentTemplate is now imported from templateService

interface LocalAgentTemplate extends AgentTemplate {
  icon: React.ReactNode;
}

const agentTemplates: LocalAgentTemplate[] = [
  {
    id: 'customer-service-hierarchy',
    name: 'Customer Service Hierarchy',
    description: 'Multi-tier customer support organization with escalation paths',
    category: 'customer-service',
    template_type: 'agent',
    estimatedTime: '30-60 minutes',
    usageCount: 156,
    tags: ['Customer Service', 'Support', 'Escalation'],
    preview: ['Service Coordinator', 'L1 Support Agent', 'L2 Support Specialist', 'Escalation Manager'],
    icon: <MessageSquare className="w-6 h-6" />,
    complexity: 'medium',
    agentCount: 6,
    features: ['Ticket Routing', 'Escalation Management', 'Knowledge Base', 'Live Chat'],
    useCase: 'Handle customer inquiries with automatic routing and escalation',
    nodes: [
      {
        id: '1',
        type: 'agentNode',
        position: { x: 250, y: 50 },
        data: {
          name: 'Customer Service Coordinator',
          role: 'coordinator',
          skills: ['Ticket Routing', 'Customer Classification', 'Load Balancing'],
          tools: ['CRM', 'Ticket System', 'Chat Platform'],
          description: 'Routes customer inquiries to appropriate agents',
          status: 'active',
          level: 0,
          department: 'Customer Service',
          maxConcurrentTasks: 100,
        } as AgentData,
      },
      {
        id: '2',
        type: 'agentNode',
        position: { x: 100, y: 200 },
        data: {
          name: 'L1 Support Agent',
          role: 'executor',
          skills: ['Basic Troubleshooting', 'Account Management', 'Documentation'],
          tools: ['Knowledge Base', 'Remote Access', 'Screen Share'],
          description: 'Handles basic customer inquiries and issues',
          status: 'active',
          level: 2,
          department: 'Customer Service',
          maxConcurrentTasks: 5,
        } as AgentData,
      },
      {
        id: '3',
        type: 'agentNode',
        position: { x: 400, y: 200 },
        data: {
          name: 'L2 Support Specialist',
          role: 'specialist',
          skills: ['Advanced Troubleshooting', 'System Integration', 'Root Cause Analysis'],
          tools: ['Diagnostic Tools', 'System Logs', 'Database Access'],
          description: 'Handles complex technical issues and escalations',
          status: 'active',
          level: 2,
          department: 'Customer Service',
          maxConcurrentTasks: 3,
        } as AgentData,
      },
      {
        id: '4',
        type: 'agentNode',
        position: { x: 250, y: 350 },
        data: {
          name: 'Escalation Manager',
          role: 'supervisor',
          skills: ['Conflict Resolution', 'Process Management', 'Customer Relations'],
          tools: ['CRM', 'Escalation Matrix', 'Communication Tools'],
          description: 'Manages escalated issues and customer complaints',
          status: 'active',
          level: 1,
          department: 'Customer Service',
          maxConcurrentTasks: 8,
        } as AgentData,
      },
    ],
    edges: [
      {
        id: 'e1-2',
        source: '1',
        target: '2',
        type: 'smoothstep',
        style: { stroke: '#10b981', strokeWidth: 2 },
        label: 'Basic Issues',
      },
      {
        id: 'e1-3',
        source: '1',
        target: '3',
        type: 'smoothstep',
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        label: 'Technical Issues',
      },
      {
        id: 'e2-4',
        source: '2',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        label: 'Escalation',
      },
      {
        id: 'e3-4',
        source: '3',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        label: 'Complex Escalation',
      },
    ],
  },
  {
    id: 'data-processing-pipeline',
    name: 'Data Processing Pipeline',
    description: 'Automated data ingestion, processing, and analytics pipeline',
    category: 'data-analytics',
    template_type: 'agent',
    estimatedTime: '45-90 minutes',
    usageCount: 89,
    tags: ['Data Processing', 'ETL', 'Analytics'],
    preview: ['Data Ingestion Agent', 'ETL Processor', 'Quality Controller', 'Analytics Engine', 'Pipeline Coordinator'],
    icon: <Database className="w-6 h-6" />,
    complexity: 'complex',
    agentCount: 5,
    features: ['Data Ingestion', 'ETL Processing', 'Quality Control', 'Analytics'],
    useCase: 'Process large volumes of data with quality checks and analytics',
    nodes: [
      {
        id: '1',
        type: 'agentNode',
        position: { x: 50, y: 100 },
        data: {
          name: 'Data Ingestion Agent',
          role: 'executor',
          skills: ['API Integration', 'File Processing', 'Data Validation'],
          tools: ['REST APIs', 'FTP', 'Database Connectors'],
          description: 'Collects data from various sources',
          status: 'active',
          level: 2,
          department: 'Data Engineering',
          maxConcurrentTasks: 10,
        } as AgentData,
      },
      {
        id: '2',
        type: 'agentNode',
        position: { x: 250, y: 100 },
        data: {
          name: 'ETL Processor',
          role: 'specialist',
          skills: ['Data Transformation', 'Schema Mapping', 'Data Cleansing'],
          tools: ['Pandas', 'Apache Spark', 'SQL'],
          description: 'Transforms and cleanses incoming data',
          status: 'active',
          level: 2,
          department: 'Data Engineering',
          maxConcurrentTasks: 5,
        } as AgentData,
      },
      {
        id: '3',
        type: 'agentNode',
        position: { x: 450, y: 100 },
        data: {
          name: 'Quality Controller',
          role: 'specialist',
          skills: ['Data Quality Assessment', 'Anomaly Detection', 'Validation Rules'],
          tools: ['Data Profiling Tools', 'Statistical Analysis', 'Alert Systems'],
          description: 'Ensures data quality and integrity',
          status: 'active',
          level: 2,
          department: 'Data Quality',
          maxConcurrentTasks: 3,
        } as AgentData,
      },
      {
        id: '4',
        type: 'agentNode',
        position: { x: 250, y: 250 },
        data: {
          name: 'Analytics Engine',
          role: 'specialist',
          skills: ['Statistical Analysis', 'Machine Learning', 'Reporting'],
          tools: ['Python', 'R', 'Tableau', 'PowerBI'],
          description: 'Performs analytics and generates insights',
          status: 'active',
          level: 2,
          department: 'Analytics',
          maxConcurrentTasks: 2,
        } as AgentData,
      },
      {
        id: '5',
        type: 'agentNode',
        position: { x: 150, y: 400 },
        data: {
          name: 'Pipeline Coordinator',
          role: 'coordinator',
          skills: ['Workflow Orchestration', 'Resource Management', 'Monitoring'],
          tools: ['Airflow', 'Monitoring Dashboard', 'Alert System'],
          description: 'Coordinates the entire data pipeline',
          status: 'active',
          level: 0,
          department: 'Data Engineering',
          maxConcurrentTasks: 20,
        } as AgentData,
      },
    ],
    edges: [
      {
        id: 'e1-2',
        source: '1',
        target: '2',
        type: 'smoothstep',
        style: { stroke: '#6366f1', strokeWidth: 2 },
        label: 'Raw Data',
      },
      {
        id: 'e2-3',
        source: '2',
        target: '3',
        type: 'smoothstep',
        style: { stroke: '#8b5cf6', strokeWidth: 2 },
        label: 'Processed Data',
      },
      {
        id: 'e3-4',
        source: '3',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#10b981', strokeWidth: 2 },
        label: 'Validated Data',
      },
      {
        id: 'e5-1',
        source: '5',
        target: '1',
        type: 'smoothstep',
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        label: 'Schedule',
      },
      {
        id: 'e5-2',
        source: '5',
        target: '2',
        type: 'smoothstep',
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        label: 'Orchestrate',
      },
    ],
  },
  {
    id: 'dev-team-structure',
    name: 'Development Team Structure',
    description: 'Software development team with code review and deployment automation',
    category: 'development',
    template_type: 'agent',
    estimatedTime: '60-120 minutes',
    usageCount: 234,
    tags: ['Development', 'CI/CD', 'Code Review'],
    preview: ['Development Coordinator', 'Code Reviewer', 'Test Automation Agent', 'Deployment Manager'],
    icon: <Brain className="w-6 h-6" />,
    complexity: 'medium',
    agentCount: 4,
    features: ['Code Review', 'CI/CD', 'Testing', 'Deployment'],
    useCase: 'Automated software development workflow with quality gates',
    nodes: [
      {
        id: '1',
        type: 'agentNode',
        position: { x: 250, y: 50 },
        data: {
          name: 'Development Coordinator',
          role: 'coordinator',
          skills: ['Project Management', 'Task Assignment', 'Code Integration'],
          tools: ['Jira', 'Git', 'Slack'],
          description: 'Coordinates development tasks and assignments',
          status: 'active',
          level: 0,
          department: 'Engineering',
          maxConcurrentTasks: 15,
        } as AgentData,
      },
      {
        id: '2',
        type: 'agentNode',
        position: { x: 100, y: 200 },
        data: {
          name: 'Code Reviewer',
          role: 'specialist',
          skills: ['Code Analysis', 'Security Review', 'Best Practices'],
          tools: ['SonarQube', 'GitHub', 'CodeClimate'],
          description: 'Reviews code for quality and security',
          status: 'active',
          level: 2,
          department: 'Engineering',
          maxConcurrentTasks: 3,
        } as AgentData,
      },
      {
        id: '3',
        type: 'agentNode',
        position: { x: 400, y: 200 },
        data: {
          name: 'Test Automation Agent',
          role: 'executor',
          skills: ['Test Execution', 'Bug Detection', 'Performance Testing'],
          tools: ['Selenium', 'Jest', 'LoadRunner'],
          description: 'Executes automated tests and reports results',
          status: 'active',
          level: 2,
          department: 'QA',
          maxConcurrentTasks: 5,
        } as AgentData,
      },
      {
        id: '4',
        type: 'agentNode',
        position: { x: 250, y: 350 },
        data: {
          name: 'Deployment Manager',
          role: 'supervisor',
          skills: ['CI/CD Management', 'Environment Control', 'Release Planning'],
          tools: ['Jenkins', 'Docker', 'Kubernetes'],
          description: 'Manages deployments and release processes',
          status: 'active',
          level: 1,
          department: 'DevOps',
          maxConcurrentTasks: 7,
        } as AgentData,
      },
    ],
    edges: [
      {
        id: 'e1-2',
        source: '1',
        target: '2',
        type: 'smoothstep',
        style: { stroke: '#8b5cf6', strokeWidth: 2 },
        label: 'Code Review',
      },
      {
        id: 'e1-3',
        source: '1',
        target: '3',
        type: 'smoothstep',
        style: { stroke: '#10b981', strokeWidth: 2 },
        label: 'Testing',
      },
      {
        id: 'e2-4',
        source: '2',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#3b82f6', strokeWidth: 2 },
        label: 'Approved Code',
      },
      {
        id: 'e3-4',
        source: '3',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#10b981', strokeWidth: 2 },
        label: 'Test Results',
      },
    ],
  },
  {
    id: 'security-incident-response',
    name: 'Security Incident Response',
    description: 'Automated security monitoring and incident response team',
    category: 'security',
    template_type: 'agent',
    estimatedTime: '90-180 minutes',
    usageCount: 45,
    tags: ['Security', 'Incident Response', 'Monitoring'],
    preview: ['Security Monitor', 'Incident Responder', 'Threat Intelligence Analyst', 'Security Coordinator'],
    icon: <Shield className="w-6 h-6" />,
    complexity: 'complex',
    agentCount: 5,
    features: ['Threat Detection', 'Incident Response', 'Forensics', 'Compliance'],
    useCase: 'Monitor, detect, and respond to security threats automatically',
    nodes: [
      {
        id: '1',
        type: 'agentNode',
        position: { x: 250, y: 50 },
        data: {
          name: 'Security Monitor',
          role: 'executor',
          skills: ['Log Analysis', 'Anomaly Detection', 'Alert Generation'],
          tools: ['SIEM', 'Splunk', 'ELK Stack'],
          description: 'Continuously monitors for security threats',
          status: 'active',
          level: 2,
          department: 'Security',
          maxConcurrentTasks: 20,
        } as AgentData,
      },
      {
        id: '2',
        type: 'agentNode',
        position: { x: 100, y: 200 },
        data: {
          name: 'Incident Responder',
          role: 'specialist',
          skills: ['Incident Analysis', 'Threat Hunting', 'Containment'],
          tools: ['Incident Response Platform', 'Network Tools', 'Forensics Kit'],
          description: 'Responds to and investigates security incidents',
          status: 'active',
          level: 2,
          department: 'Security',
          maxConcurrentTasks: 3,
        } as AgentData,
      },
      {
        id: '3',
        type: 'agentNode',
        position: { x: 400, y: 200 },
        data: {
          name: 'Threat Intelligence Analyst',
          role: 'specialist',
          skills: ['Threat Intelligence', 'IOC Analysis', 'Attribution'],
          tools: ['Threat Intel Platforms', 'MISP', 'VirusTotal'],
          description: 'Analyzes threats and provides intelligence',
          status: 'active',
          level: 2,
          department: 'Security',
          maxConcurrentTasks: 2,
        } as AgentData,
      },
      {
        id: '4',
        type: 'agentNode',
        position: { x: 250, y: 350 },
        data: {
          name: 'Security Coordinator',
          role: 'coordinator',
          skills: ['Incident Coordination', 'Communication', 'Escalation'],
          tools: ['Communication Platform', 'Ticketing System', 'Dashboard'],
          description: 'Coordinates security response activities',
          status: 'active',
          level: 0,
          department: 'Security',
          maxConcurrentTasks: 10,
        } as AgentData,
      },
    ],
    edges: [
      {
        id: 'e1-4',
        source: '1',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#ef4444', strokeWidth: 2 },
        label: 'Alert',
      },
      {
        id: 'e4-2',
        source: '4',
        target: '2',
        type: 'smoothstep',
        style: { stroke: '#f59e0b', strokeWidth: 2 },
        label: 'Investigate',
      },
      {
        id: 'e4-3',
        source: '4',
        target: '3',
        type: 'smoothstep',
        style: { stroke: '#8b5cf6', strokeWidth: 2 },
        label: 'Analyze',
      },
      {
        id: 'e2-4',
        source: '2',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#10b981', strokeWidth: 2 },
        label: 'Report',
      },
    ],
  },
];

const categoryIcons = {
  enterprise: <Building2 className="w-5 h-5" />,
  development: <Brain className="w-5 h-5" />,
  'customer-service': <MessageSquare className="w-5 h-5" />,
  'data-analytics': <Database className="w-5 h-5" />,
  security: <Shield className="w-5 h-5" />,
};

const complexityColors = {
  simple: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  complex: 'bg-red-100 text-red-800',
};

export const AgentTemplates: React.FC = () => {
  const { setAgentData } = useAppStore();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<LocalAgentTemplate | null>(null);
  const [availableTemplates, setAvailableTemplates] = useState<LocalAgentTemplate[]>([]);
  const [apiTemplates, setApiTemplates] = useState<any[]>([]); // Store original API data for cloning
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>(['all']);
  
  // Delete confirmation state
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    template: LocalAgentTemplate | null;
    isLoading: boolean;
  }>({ isOpen: false, template: null, isLoading: false });
  
  // Clone loading state
  const [cloningTemplateId, setCloningTemplateId] = useState<string | null>(null);

  // Load available templates on component mount
  useEffect(() => {
    const fetchAgentTemplates = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch templates from database API
        const response = await templatesApiService.fetchAgentTemplates(100); // Fetch up to 100 templates
        
        // Store original API data for cloning
        setApiTemplates(response.templates);
        
        // Convert API responses to frontend format
        const apiTemplates = response.templates.map(apiTemplate => {
          const converted = templatesApiService.convertApiToAgentTemplate(apiTemplate);
          return {
            ...converted,
            icon: categoryIcons[converted.category as keyof typeof categoryIcons] || <Users className="w-6 h-6" />
          } as LocalAgentTemplate;
        });
        
        console.log(`🎯 Agent Templates: Loaded ${apiTemplates.length} templates from database`);
        console.log(`🎯 Agent Templates: Template names:`, apiTemplates.map(t => t.name));
        
        // Use database templates exclusively (don't mix with hardcoded templates)
        setAvailableTemplates(apiTemplates);
        
        // Update categories from API response
        const responseCategories = response.categories || [];
        const templateCategories = Array.from(new Set(apiTemplates.map(t => t.category)));
        const allCategories = ['all', ...responseCategories, ...templateCategories];
        const uniqueCategories = Array.from(new Set(allCategories));
        setCategories(uniqueCategories);
        
        console.log(`🎯 Agent Templates: Categories found:`, uniqueCategories);
        
      } catch (err) {
        console.error('Failed to fetch agent templates:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load agent templates. Please try again later.';
        setError(errorMessage);
        
        // Fallback to built-in templates if API fails
        console.warn('🔄 Agent Templates: API failed, falling back to built-in templates');
        try {
          const serviceTemplates = templateService.getAllAgentTemplates();
          const templatesWithIcons: LocalAgentTemplate[] = serviceTemplates.map(template => ({
            ...template,
            icon: categoryIcons[template.category as keyof typeof categoryIcons] || <Users className="w-6 h-6" />
          }));
          
          // Use hardcoded templates only as fallback (not mixed with database)
          const fallbackTemplates = [...agentTemplates, ...templatesWithIcons];
          setAvailableTemplates(fallbackTemplates);
          
          // Extract categories from fallback templates
          const templateCategories = Array.from(new Set(fallbackTemplates.map(t => t.category)));
          setCategories(['all', ...templateCategories]);
          
          console.log(`🎯 Agent Templates: Fallback loaded ${fallbackTemplates.length} built-in templates`);
        } catch (fallbackErr) {
          console.error('Fallback also failed:', fallbackErr);
          // Use just the hardcoded templates as last resort
          setAvailableTemplates(agentTemplates);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAgentTemplates();
  }, []);

  const filteredTemplates = selectedCategory === 'all' 
    ? availableTemplates 
    : availableTemplates.filter(template => template.category === selectedCategory);

  const handleTemplateLoad = (template: LocalAgentTemplate) => {
    setAgentData({
      nodes: template.nodes,
      edges: template.edges,
    });
    
    // Navigate to the Agent Designer (assuming there's a way to switch tabs)
    const { setActiveTab } = useAppStore.getState();
    setActiveTab('designer'); // This should switch to the Agent Designer tab
  };

  const handleCloneTemplate = async (template: LocalAgentTemplate) => {
    try {
      // Set loading state
      setCloningTemplateId(template.id);
      
      // Find the original API template data
      const originalApiTemplate = apiTemplates.find(api => api.id === template.id);
      if (!originalApiTemplate) {
        alert('Original template data not found. Please refresh and try again.');
        return;
      }

      // Clone the template using the API
      const clonedTemplate = await templatesApiService.cloneAgentTemplate(originalApiTemplate);
      
      // Convert the new template to frontend format and add to the list
      const convertedClone = templatesApiService.convertApiToAgentTemplate(clonedTemplate);
      const cloneWithIcon = {
        ...convertedClone,
        icon: categoryIcons[convertedClone.category as keyof typeof categoryIcons] || <Users className="w-6 h-6" />
      } as LocalAgentTemplate;
      
      setAvailableTemplates(prev => [cloneWithIcon, ...prev]);
      setApiTemplates(prev => [clonedTemplate, ...prev]);
      
      alert('Template cloned successfully!');
    } catch (error) {
      console.error('Failed to clone template:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to clone template';
      alert(errorMessage);
    } finally {
      // Clear loading state
      setCloningTemplateId(null);
    }
  };


  const handleDeleteTemplate = (template: LocalAgentTemplate) => {
    setDeleteConfirm({
      isOpen: true,
      template: template,
      isLoading: false
    });
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirm.template) return;

    setDeleteConfirm(prev => ({ ...prev, isLoading: true }));

    try {
      // Note: Agent template delete endpoint doesn't exist yet
      const result = await templatesApiService.deleteAgentTemplate(deleteConfirm.template.id);
      
      // Remove template from local state
      setAvailableTemplates(prev => prev.filter(t => t.id !== deleteConfirm.template!.id));
      
      // Close dialog
      setDeleteConfirm({ isOpen: false, template: null, isLoading: false });
      
      // Show success message
      alert(result.message || 'Agent template deleted successfully!');
      
    } catch (error) {
      console.error('Failed to delete agent template:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete agent template';
      alert(errorMessage);
      
      // Reset loading state but keep dialog open
      setDeleteConfirm(prev => ({ ...prev, isLoading: false }));
    }
  };

  const handleCancelDelete = () => {
    setDeleteConfirm({ isOpen: false, template: null, isLoading: false });
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Agent Organization Templates</h2>
          <p className="text-gray-600">
            Choose from pre-built multi-agent organization templates or create your own custom structure
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 animate-spin text-fuschia-500" />
          <span className="ml-2 text-gray-600">Loading agent templates...</span>
        </div>
      </div>
    );
  }

  if (error && availableTemplates.length === 0) {
    return (
      <div className="p-6">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Agent Organization Templates</h2>
          <p className="text-gray-600">
            Choose from pre-built multi-agent organization templates or create your own custom structure
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600 mb-2">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Agent Organization Templates</h2>
        <p className="text-gray-600">
          Choose from pre-built multi-agent organization templates or create your own custom structure
        </p>
        {error && (
          <div className="mt-2 p-2 bg-yellow-100 border border-yellow-400 rounded text-yellow-800 text-sm">
            ⚠️ {error} (Showing available templates)
          </div>
        )}
      </div>

      {/* Category Filter */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-sm font-medium text-gray-700">Category:</span>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                selectedCategory === category
                  ? 'bg-fuschia-100 text-fuschia-800 border border-fuschia-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <div className="flex items-center space-x-1">
                {category !== 'all' && categoryIcons[category as keyof typeof categoryIcons]}
                <span>{category === 'all' ? 'All' : category.charAt(0).toUpperCase() + category.slice(1).replace('-', ' ')}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    {template.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{template.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={cn(
                        'px-2 py-1 text-xs font-medium rounded-full',
                        complexityColors[template.complexity]
                      )}>
                        {template.complexity}
                      </span>
                      <span className="text-xs text-gray-500">
                        {template.agentCount} agents
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span className="text-sm text-gray-600">4.8</span>
                </div>
              </div>

              {/* Description */}
              <p className="text-gray-600 text-sm mb-4">{template.description}</p>

              {/* Use Case */}
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-700 mb-1">Use Case:</h4>
                <p className="text-xs text-gray-600">{template.useCase}</p>
              </div>

              {/* Features */}
              <div className="mb-6">
                <h4 className="text-xs font-medium text-gray-700 mb-2">Features:</h4>
                <div className="flex flex-wrap gap-1">
                  {template.features.slice(0, 3).map((feature, index) => (
                    <span
                      key={index}
                      className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded border"
                    >
                      {feature}
                    </span>
                  ))}
                  {template.features.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{template.features.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleTemplateLoad(template)}
                  className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
                >
                  <Play className="w-4 h-4" />
                  <span>Use Template</span>
                </button>
                <button
                  onClick={() => handleCloneTemplate(template)}
                  disabled={cloningTemplateId === template.id}
                  className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title={cloningTemplateId === template.id ? "Cloning template..." : "Clone template"}
                >
                  {cloningTemplateId === template.id ? (
                    <Loader className="w-4 h-4 animate-spin" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
                <button className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteTemplate(template)}
                  className="p-2 text-red-500 hover:text-red-700 border border-red-300 rounded-md hover:bg-red-50 transition-colors"
                  title="Delete template"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Template Preview Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">{selectedTemplate.name}</h3>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <p className="text-gray-600">{selectedTemplate.description}</p>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Agent Roles:</h4>
                  <div className="space-y-2">
                    {selectedTemplate.nodes.map((node) => (
                      <div key={node.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                        <div className="w-8 h-8 bg-fuschia-100 rounded-full flex items-center justify-center">
                          <Users className="w-4 h-4 text-fuschia-600" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{node.data.name}</div>
                          <div className="text-sm text-gray-600">{node.data.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      handleTemplateLoad(selectedTemplate);
                      setSelectedTemplate(null);
                    }}
                    className="flex-1 px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
                  >
                    Use This Template
                  </button>
                  <button
                    onClick={() => setSelectedTemplate(null)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        title="Delete Agent Template"
        message={`Are you sure you want to delete "${deleteConfirm.template?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={deleteConfirm.isLoading}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
      />
    </div>
  );
};