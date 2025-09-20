import React, { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Panel,
  Handle,
  Position,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Plus, Users, Save, Upload, Trash2, Settings, CheckCircle2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAppStore } from '@/store/appStore';
import { Drawer } from '@/components/ui/Drawer';
import { AgentPropertyForm } from './AgentPropertyForm';
import { templateService, AgentTemplate } from '@/services/templateService';
import { agentService } from '@/services/agentService';

// Define agent tool structure (matching backend AgentTool model)
export interface AgentTool {
  name: string;
  description: string;
  parameters: Record<string, any>;
  required_permissions: string[];
  tool_type: string;
  configuration: Record<string, any>;
}

// Define agent data types
export interface AgentData {
  name: string;
  role: 'supervisor' | 'specialist' | 'coordinator' | 'executor';
  skills: string[];
  tools: string[]; // Tool names for UI display
  agentTools?: AgentTool[]; // Structured tools for backend
  description: string;
  status: 'active' | 'idle' | 'busy' | 'offline';
  level: number; // 0 = entry point, 1 = supervisor, 2 = specialist
  department?: string;
  maxConcurrentTasks?: number;
  strategy?: 'simple' | 'chain_of_thought' | 'react' | 'hybrid';
}

// Custom agent node component
const AgentNode: React.FC<{ data: AgentData; selected: boolean }> = ({ data, selected }) => {
  const getRoleColor = () => {
    switch (data.role) {
      case 'supervisor':
        return 'bg-purple-100 border-purple-300 text-purple-800';
      case 'specialist':
        return 'bg-blue-100 border-blue-300 text-blue-800';
      case 'coordinator':
        return 'bg-green-100 border-green-300 text-green-800';
      case 'executor':
        return 'bg-orange-100 border-orange-300 text-orange-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const getStatusIndicator = () => {
    switch (data.status) {
      case 'active':
        return <div className="w-3 h-3 bg-green-500 rounded-full" />;
      case 'busy':
        return <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />;
      case 'idle':
        return <div className="w-3 h-3 bg-blue-500 rounded-full" />;
      case 'offline':
        return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
      default:
        return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
    }
  };

  const getLevelBadge = () => {
    const levelLabels = { 0: 'Entry', 1: 'L1', 2: 'L2', 3: 'L3' };
    return levelLabels[data.level as keyof typeof levelLabels] || 'L?';
  };

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[220px] max-w-[280px] shadow-sm relative bg-white',
        getRoleColor(),
        selected && 'ring-2 ring-fuschia-500'
      )}
    >
      {/* Input Handle - only show if not level 0 */}
      {data.level > 0 && (
        <Handle
          type="target"
          position={Position.Top}
          className="!bg-gray-600 !border-2 !border-white !w-3 !h-3"
        />
      )}
      
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIndicator()}
          <span className="text-xs font-semibold uppercase tracking-wide">
            {data.role}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-xs bg-white px-2 py-1 rounded-full font-medium">
            {getLevelBadge()}
          </span>
        </div>
      </div>
      
      {/* Agent Name */}
      <div className="font-bold text-sm mb-2">{data.name}</div>
      
      {/* Department */}
      {data.department && (
        <div className="text-xs text-gray-600 mb-2">
          📁 {data.department}
        </div>
      )}
      
      {/* Description */}
      {data.description && (
        <div className="text-xs text-gray-600 mb-3 leading-tight">
          {data.description}
        </div>
      )}
      
      {/* Skills */}
      {data.skills.length > 0 && (
        <div className="mb-2">
          <div className="text-xs font-medium text-gray-700 mb-1">Skills:</div>
          <div className="flex flex-wrap gap-1">
            {data.skills.slice(0, 3).map((skill, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded border"
              >
                {skill}
              </span>
            ))}
            {data.skills.length > 3 && (
              <span className="text-xs text-gray-500">+{data.skills.length - 3}</span>
            )}
          </div>
        </div>
      )}
      
      {/* Tools */}
      {data.tools.length > 0 && (
        <div className="mb-2">
          <div className="text-xs font-medium text-gray-700 mb-1">Tools:</div>
          <div className="flex flex-wrap gap-1">
            {data.tools.slice(0, 2).map((tool, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 text-xs bg-green-50 text-green-700 rounded border"
              >
                {tool}
              </span>
            ))}
            {data.tools.length > 2 && (
              <span className="text-xs text-gray-500">+{data.tools.length - 2}</span>
            )}
          </div>
        </div>
      )}
      
      {/* Concurrent Tasks */}
      {data.maxConcurrentTasks && (
        <div className="text-xs text-gray-500">
          Max tasks: {data.maxConcurrentTasks}
        </div>
      )}
      
      {/* Output Handle - only show if not highest level specialist */}
      {data.level < 3 && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!bg-gray-600 !border-2 !border-white !w-3 !h-3"
        />
      )}
    </div>
  );
};

// Node types
const nodeTypes = {
  agentNode: AgentNode,
};

// Initial agents
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'agentNode',
    position: { x: 250, y: 50 },
    data: {
      name: 'Central Coordinator',
      role: 'coordinator',
      skills: ['Task Routing', 'Load Balancing', 'Orchestration'],
      tools: ['Workflow Engine', 'Queue Manager'],
      description: 'Routes incoming requests to appropriate specialist agents',
      status: 'active',
      level: 0,
      department: 'Operations',
      maxConcurrentTasks: 50,
    },
  },
  {
    id: '2',
    type: 'agentNode',
    position: { x: 100, y: 200 },
    data: {
      name: 'Data Supervisor',
      role: 'supervisor',
      skills: ['Data Processing', 'ETL Operations', 'Quality Control'],
      tools: ['Pandas', 'SQL', 'Apache Spark'],
      description: 'Supervises data-related operations and processing tasks',
      status: 'active',
      level: 1,
      department: 'Data',
      maxConcurrentTasks: 10,
    },
  },
  {
    id: '3',
    type: 'agentNode',
    position: { x: 400, y: 200 },
    data: {
      name: 'Communication Supervisor',
      role: 'supervisor',
      skills: ['Email Processing', 'Slack Integration', 'Notifications'],
      tools: ['SMTP', 'Slack API', 'Teams API'],
      description: 'Manages all communication and notification tasks',
      status: 'active',
      level: 1,
      department: 'Communications',
      maxConcurrentTasks: 15,
    },
  },
  {
    id: '4',
    type: 'agentNode',
    position: { x: 50, y: 350 },
    data: {
      name: 'Database Specialist',
      role: 'specialist',
      skills: ['SQL Queries', 'Database Design', 'Performance Tuning'],
      tools: ['PostgreSQL', 'MongoDB', 'Redis'],
      description: 'Handles complex database operations and optimizations',
      status: 'idle',
      level: 2,
      department: 'Data',
      maxConcurrentTasks: 5,
    },
  },
  {
    id: '5',
    type: 'agentNode',
    position: { x: 150, y: 350 },
    data: {
      name: 'Analytics Specialist',
      role: 'specialist',
      skills: ['Statistical Analysis', 'Machine Learning', 'Reporting'],
      tools: ['Python', 'R', 'Tableau'],
      description: 'Performs advanced analytics and generates insights',
      status: 'busy',
      level: 2,
      department: 'Data',
      maxConcurrentTasks: 3,
    },
  },
];

// Initial edges
const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'smoothstep',
    style: { stroke: '#8b5cf6', strokeWidth: 2 },
    label: 'Data Tasks',
  },
  {
    id: 'e1-3',
    source: '1',
    target: '3',
    type: 'smoothstep',
    style: { stroke: '#8b5cf6', strokeWidth: 2 },
    label: 'Communication Tasks',
  },
  {
    id: 'e2-4',
    source: '2',
    target: '4',
    type: 'smoothstep',
    style: { stroke: '#3b82f6', strokeWidth: 2 },
    label: 'DB Operations',
  },
  {
    id: 'e2-5',
    source: '2',
    target: '5',
    type: 'smoothstep',
    style: { stroke: '#3b82f6', strokeWidth: 2 },
    label: 'Analytics',
  },
];

interface AgentDesignerProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
}

export const AgentDesigner: React.FC<AgentDesignerProps> = ({ 
  initialNodes: propInitialNodes, 
  initialEdges: propInitialEdges 
}) => {
  const { agentData } = useAppStore();
  
  // Use agentData from store if available, then prop nodes/edges, otherwise use default
  const defaultNodes = agentData?.nodes || propInitialNodes || initialNodes;
  const defaultEdges = agentData?.edges || propInitialEdges || initialEdges;
  
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges);
  const [selectedAgent, setSelectedAgent] = useState<Node | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [availableTemplates, setAvailableTemplates] = useState<AgentTemplate[]>([]);
  const [showTemplateLoader, setShowTemplateLoader] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveFormData, setSaveFormData] = useState({
    name: '',
    description: '',
    category: 'Custom',
    folder: '',
  });
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [isPropertiesDialogOpen, setIsPropertiesDialogOpen] = useState(false);
  const [currentTemplateId, setCurrentTemplateId] = useState<string | null>(null);
  const [databaseConnectionError, setDatabaseConnectionError] = useState<string | null>(null);
  
  // Canvas update notification state
  const [canvasUpdateNotification, setCanvasUpdateNotification] = useState<{
    show: boolean;
    message: string;
    timestamp: number;
  } | null>(null);
  
  // Agent metadata state
  const [agentMetadata, setAgentMetadata] = useState({
    name: 'Untitled Agent Network',
    description: 'Describe what this agent organization does...',
    category: 'Custom',
    agentCount: 0,
    connectionCount: 0,
  });

  // AgentTemplate is now imported from templateService


  // Update nodes and edges when agentData changes
  useEffect(() => {
    if (agentData?.nodes && agentData?.edges) {
      const previousNodeCount = nodes.length;
      const newNodeCount = agentData.nodes.length;
      
      setNodes(agentData.nodes);
      setEdges(agentData.edges);
      
      // Show canvas update notification if this seems to be an external update
      if (previousNodeCount > 0 && newNodeCount !== previousNodeCount) {
        setCanvasUpdateNotification({
          show: true,
          message: `Agent organization updated: ${newNodeCount} agents, ${agentData.edges.length} connections`,
          timestamp: Date.now()
        });
        
        // Auto-hide notification after 5 seconds
        setTimeout(() => {
          setCanvasUpdateNotification(null);
        }, 5000);
      }
    }
  }, [agentData, setNodes, setEdges, nodes.length]);

  // Load available templates and categories from database only
  useEffect(() => {
    const loadTemplatesFromDatabase = async () => {
      setIsLoading(true);
      try {
        // Fetch agent templates from database
        const databaseTemplates = await agentService.getAgentTemplatesFromDatabase();
        console.log('Raw templates from database:', databaseTemplates);
        
        setAvailableTemplates(databaseTemplates);
        
        // Extract categories from database templates
        const categories = Array.from(new Set(databaseTemplates.map(t => t.category)));
        setAvailableCategories(categories);
        
        // Clear any previous database connection error
        setDatabaseConnectionError(null);
        
        console.log(`Loaded ${databaseTemplates.length} agent templates from database`);
      } catch (error) {
        console.error('Failed to load templates from database:', error);
        // Show error message instead of falling back to local storage
        setAvailableTemplates([]);
        setAvailableCategories([]);
        setDatabaseConnectionError(error instanceof Error ? error.message : 'Failed to connect to database');
      } finally {
        setIsLoading(false);
      }
    };

    loadTemplatesFromDatabase();
  }, []);

  // Update metadata when nodes/edges change
  useEffect(() => {
    setAgentMetadata(prev => ({
      ...prev,
      agentCount: nodes.length,
      connectionCount: edges.length,
    }));
  }, [nodes.length, edges.length]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({
      ...params,
      type: 'smoothstep',
      style: { stroke: '#8b5cf6', strokeWidth: 2 },
    }, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedAgent(node);
    setIsDrawerOpen(true);
  }, []);

  const handleAgentUpdate = useCallback((nodeId: string, newData: Partial<AgentData>) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...newData } }
          : node
      )
    );
  }, [setNodes]);

  const handleDrawerClose = useCallback(() => {
    setIsDrawerOpen(false);
    setSelectedAgent(null);
  }, []);

  const addNewAgent = useCallback(() => {
    const newAgent: Node = {
      id: `${nodes.length + 1}`,
      type: 'agentNode',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      data: {
        name: 'New Agent',
        role: 'executor',
        skills: [],
        tools: [],
        description: 'Configure this agent',
        status: 'offline',
        level: 2,
        department: 'General',
        maxConcurrentTasks: 1,
      },
    };
    setNodes((nds) => [...nds, newAgent]);
  }, [nodes.length, setNodes]);

  const showSaveAgentDialog = useCallback(() => {
    // Initialize form with current agent metadata (like WorkflowDesigner)
    setSaveFormData({
      name: agentMetadata.name !== 'Untitled Agent Network' ? agentMetadata.name : `Agent Network ${new Date().toLocaleDateString()}`,
      description: agentMetadata.description !== 'Describe what this agent organization does...' ? agentMetadata.description : 'Custom agent organization created in designer',
      category: agentMetadata.category || 'Custom',
      folder: '',
    });
    setShowSaveDialog(true);
  }, [agentMetadata]);

  const saveAgentAsTemplate = useCallback(async () => {
    if (!saveFormData.name.trim()) {
      alert('Please enter a name for the template');
      return;
    }

    try {
      // Determine complexity based on agent count and connections
      let complexity: 'Simple' | 'Medium' | 'Advanced' = 'Simple';
      if (nodes.length > 3 || edges.length > 4) {
        complexity = 'Medium';
      }
      if (nodes.length > 6 || edges.length > 8) {
        complexity = 'Advanced';
      }

      // Extract features from agent skills
      const allSkills = nodes.flatMap(node => node.data?.skills || []);
      const uniqueSkills = [...new Set(allSkills)];
      const features = uniqueSkills.slice(0, 4); // Take top 4 unique skills as features

      // Create use case description
      const useCase = `Multi-agent organization with ${nodes.length} specialized agents for ${saveFormData.category.toLowerCase()} operations`;

      // Estimate time based on complexity
      const estimatedTime = complexity === 'Simple' ? '15-30 minutes' : 
                           complexity === 'Medium' ? '30-60 minutes' : 
                           '60+ minutes';

      // Create agent template using the generic templateService
      const template = templateService.createTemplateFromAgent(
        saveFormData.name,
        saveFormData.description,
        saveFormData.category,
        nodes,
        edges,
        features,
        useCase
      );

      // Override complexity and estimated time
      template.complexity = complexity;
      template.estimatedTime = estimatedTime;

      try {
        // First try to save to database
        const isConnected = await agentService.testConnection();
        if (isConnected) {
          const savedTemplate = await agentService.saveAgentTemplateToDatabase({
            id: currentTemplateId, // Pass current template ID for upsert logic
            name: saveFormData.name,
            description: saveFormData.description,
            category: saveFormData.category,
            complexity,
            estimatedTime,
            tags: template.tags,
            agentCount: nodes.length,
            features,
            useCase,
            nodes: nodes.map(node => ({ ...node, selected: false, dragging: false })),
            edges: edges.map(edge => ({ ...edge, selected: false }))
          });

          // Also save as file if requested
          if (saveFormData.folder.trim()) {
            templateService.saveTemplateToFile(template);
          }

          // Close dialog and show success
          setShowSaveDialog(false);
          const operation = currentTemplateId ? 'updated' : 'created';
          alert(`Agent template \"${savedTemplate.name}\" ${operation} successfully in database!\\nID: ${savedTemplate.id}`);
          
          // Update current template ID if it was a new creation
          if (!currentTemplateId) {
            setCurrentTemplateId(savedTemplate.id);
          }
          
          // Update the app store with the current state to refresh task descriptions
          const { setAgentData } = useAppStore.getState();
          setAgentData({
            nodes: nodes.map(node => ({ ...node, selected: false, dragging: false })),
            edges: edges.map(edge => ({ ...edge, selected: false })),
            metadata: agentMetadata
          });
        } else {
          throw new Error('Database connection failed. Please ensure the backend server is running.');
        }
      } catch (dbError) {
        console.error('Database save failed:', dbError);
        
        // Show error message instead of falling back to local storage
        alert(`Failed to save agent template: ${dbError instanceof Error ? dbError.message : 'Database connection failed'}\\n\\nPlease ensure the backend server is running and try again.`);
        return; // Don't close dialog, let user retry
      }

      // Reload templates from database to reflect the save
      try {
        const databaseTemplates = await agentService.getAgentTemplatesFromDatabase();
        setAvailableTemplates(databaseTemplates);
      } catch (error) {
        console.warn('Failed to reload templates after save:', error);
      }
      
      // Reset form
      setSaveFormData({
        name: '',
        description: '',
        category: 'Custom',
        folder: '',
      });

    } catch (error) {
      console.error('Failed to save agent template:', error);
      alert(`Failed to save template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [saveFormData, nodes, edges]);

  const showLoadDialog = useCallback(() => {
    setShowTemplateLoader(true);
  }, []);

  // Helper function to validate and process template data
  const validateAndProcessTemplate = useCallback((template: AgentTemplate) => {
    console.log('Processing template:', template);
    
    // Validate template structure
    if (!template.name || !template.id) {
      throw new Error('Invalid template: missing name or id');
    }
    
    // Ensure nodes array exists and has proper structure
    const nodes = template.nodes || [];
    const edges = template.edges || [];
    
    console.log('Template has', nodes.length, 'nodes,', edges.length, 'edges');
    
    return {
      ...template,
      nodes,
      edges
    };
  }, []);

  const loadAgentTemplate = useCallback((template: AgentTemplate) => {
    try {
      console.log('Loading agent template:', template);
      
      // Validate and process template data
      const processedTemplate = validateAndProcessTemplate(template);
      console.log('Processed template:', processedTemplate);
      console.log('Template nodes sample:', processedTemplate.nodes?.slice(0, 2));
      console.log('Template edges sample:', processedTemplate.edges?.slice(0, 2));
      
      // Clear existing canvas first
      setNodes([]);
      setEdges([]);
      
      // Set current template ID for potential updates
      setCurrentTemplateId(processedTemplate.id);
      
      // Update agent metadata with template information (like WorkflowDesigner)
      setAgentMetadata({
        name: processedTemplate.name,
        description: processedTemplate.description,
        category: processedTemplate.category || 'Custom',
        agentCount: processedTemplate.nodes?.length || 0,
        connectionCount: processedTemplate.edges?.length || 0,
      });
    
    // Small delay to ensure clearing is visible and proper ReactFlow update
    setTimeout(() => {
      // If template has pre-defined nodes and edges, use them directly
      if (processedTemplate.nodes && processedTemplate.nodes.length > 0) {
        console.log('Loading template with nodes:', processedTemplate.nodes.length, 'edges:', processedTemplate.edges?.length || 0);
        
        // Ensure nodes have the correct type and position for ReactFlow
        const processedNodes = processedTemplate.nodes.map((node, index) => {
          // Transform backend agent data format to ReactFlow format
          let nodeData;
          if (node.data) {
            // If data is already in ReactFlow format, use it
            nodeData = node.data;
          } else {
            // Transform backend format to ReactFlow format
            nodeData = {
              name: node.name || 'Unnamed Agent',
              role: node.role || 'executor',
              skills: node.capabilities?.map((cap: any) => cap.name) || [],
              tools: node.tools?.map((tool: any) => tool.name) || [],
              description: node.description || '',
              status: node.status || 'active',
              level: node.level !== undefined ? node.level : 2,
              department: node.department || 'General',
              maxConcurrentTasks: node.max_concurrent_tasks || 3,
              strategy: node.strategy || 'hybrid'
            };
          }

          return {
            id: node.id || `node-${index}`, // Ensure node has an ID
            type: node.type || 'agentNode', // Ensure type is set
            position: node.position || { x: 100 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 200 }, // Ensure position exists
            data: nodeData, // Use transformed data
            selected: false, // Clear any selection state
            dragging: false // Clear any dragging state
          };
        });
        
        const processedEdges = (processedTemplate.edges || []).map((edge, index) => {
          // Transform backend connection data format to ReactFlow format
          const source = edge.source || edge.from_agent_id || '';
          const target = edge.target || edge.to_agent_id || '';
          
          return {
            id: edge.id || `edge-${source}-${target}` || `edge-${index}`, // Ensure edge has an ID
            source: source, // Use transformed source
            target: target, // Use transformed target
            type: edge.type || edge.connection_type || 'smoothstep', // Default edge type
            style: edge.style || { stroke: '#8b5cf6', strokeWidth: 2 }, // Default style
            label: edge.label || '', // Optional label
            selected: false // Clear any selection state
          };
        });
        
        console.log('Final processed nodes sample:', processedNodes.slice(0, 2));
        console.log('Node data transformation:', {
          original: processedTemplate.nodes?.slice(0, 1),
          transformed: processedNodes.slice(0, 1)
        });
        console.log('Final processed edges sample:', processedEdges.slice(0, 2));
        console.log('Edge data transformation:', {
          original: processedTemplate.edges?.slice(0, 1),
          transformed: processedEdges.slice(0, 1)
        });
        
        setNodes(processedNodes);
        setEdges(processedEdges);
        
        // Additional small delay to ensure ReactFlow processes the new nodes and update metadata
        setTimeout(() => {
          // Update metadata with actual loaded node/edge counts
          setAgentMetadata(prev => ({
            ...prev,
            agentCount: processedNodes.length,
            connectionCount: processedEdges.length,
          }));
          console.log('Template loaded and rendered with', processedNodes.length, 'nodes');
        }, 50);
      } else {
        // Fallback: Create agent nodes based on template characteristics
        console.log('Creating fallback nodes for template:', processedTemplate.name);
        const agentNodes = createAgentNetworkFromTemplate(processedTemplate);
        const agentEdges = createAgentEdgesFromTemplate(processedTemplate, agentNodes);
        
        setNodes(agentNodes);
        setEdges(agentEdges);
        
        // Update metadata with actual loaded node/edge counts
        setTimeout(() => {
          setAgentMetadata(prev => ({
            ...prev,
            agentCount: agentNodes.length,
            connectionCount: agentEdges.length,
          }));
          console.log('Fallback template loaded with', agentNodes.length, 'nodes');
        }, 50);
      }
      
      console.log(`Loaded agent template: ${processedTemplate.name}`);
    }, 100);
    
    setShowTemplateLoader(false);
    } catch (error) {
      console.error('Failed to load agent template:', error);
      alert(`Failed to load template: ${error instanceof Error ? error.message : 'Invalid template format'}`);
      setShowTemplateLoader(false);
    }
  }, [setNodes, setEdges, validateAndProcessTemplate]);

  const handleFileLoad = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setIsLoading(true);
      const template = await templateService.loadTemplateFromFile<AgentTemplate>(file);
      
      // Validate that it's an agent template
      if (template.template_type !== 'agent') {
        throw new Error('Invalid template type. Please select an agent template file.');
      }
      
      loadAgentTemplate(template);
    } catch (error) {
      alert(`Failed to load template file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
      // Reset file input
      event.target.value = '';
    }
  }, [loadAgentTemplate]);

  const clearCanvas = useCallback(() => {
    if (confirm('Are you sure you want to clear the canvas? This will remove all agents and connections.')) {
      setNodes([]);
      setEdges([]);
      setSelectedAgent(null);
      setIsDrawerOpen(false);
      setCurrentTemplateId(null); // Clear current template ID for new template
      
      // Reset metadata for new template
      setAgentMetadata({
        name: 'Untitled Agent Network',
        description: 'Describe what this agent organization does...',
        category: 'Custom',
        agentCount: 0,
        connectionCount: 0,
      });
    }
  }, [setNodes, setEdges]);

  const handlePropertiesEdit = useCallback(() => {
    setIsPropertiesDialogOpen(true);
  }, []);

  const handlePropertiesSave = useCallback(() => {
    // Sync with app store if needed
    const { setAgentData } = useAppStore.getState();
    const currentAgentData = useAppStore.getState().agentData;
    
    if (currentAgentData) {
      setAgentData({
        ...currentAgentData,
        metadata: {
          ...currentAgentData.metadata,
          name: agentMetadata.name,
          description: agentMetadata.description,
          category: agentMetadata.category,
        }
      });
    }
    
    setIsPropertiesDialogOpen(false);
  }, [agentMetadata]);

  const handlePropertiesCancel = useCallback(() => {
    // Revert to original values if they exist in the store
    const currentAgentData = useAppStore.getState().agentData;
    if (currentAgentData?.metadata) {
      setAgentMetadata(prev => ({
        ...prev,
        name: currentAgentData.metadata?.name || 'Untitled Agent Network',
        description: currentAgentData.metadata?.description || 'Describe what this agent organization does...',
        category: currentAgentData.metadata?.category || 'Custom',
      }));
    }
    setIsPropertiesDialogOpen(false);
  }, []);

  // Helper function to create agent network from AgentTemplate
  const createAgentNetworkFromTemplate = (template: AgentTemplate): Node[] => {
    const agents: Node[] = [];
    const category = template.category.toLowerCase();

    // Create agents based on template category
    switch (category) {
      case 'customer-service':
        agents.push(
          {
            id: '1',
            type: 'agentNode',
            position: { x: 250, y: 50 },
            data: {
              name: 'Customer Service Coordinator',
              role: 'coordinator' as const,
              skills: ['Ticket Routing', 'Customer Classification', 'Load Balancing'],
              tools: [],
              description: 'Routes customer inquiries to appropriate agents',
              status: 'active' as const,
              level: 0,
              department: 'Customer Service',
              maxConcurrentTasks: 100,
            },
          },
          {
            id: '2',
            type: 'agentNode',
            position: { x: 100, y: 200 },
            data: {
              name: 'L1 Support Agent',
              role: 'executor' as const,
              skills: ['Basic Troubleshooting', 'Account Management', 'Documentation'],
              tools: [],
              description: 'Handles basic customer inquiries and issues',
              status: 'active' as const,
              level: 2,
              department: 'Customer Service',
              maxConcurrentTasks: 5,
            },
          },
          {
            id: '3',
            type: 'agentNode',
            position: { x: 400, y: 200 },
            data: {
              name: 'L2 Support Specialist',
              role: 'specialist' as const,
              skills: ['Advanced Troubleshooting', 'System Integration', 'Root Cause Analysis'],
              tools: [],
              description: 'Handles complex technical issues and escalations',
              status: 'active' as const,
              level: 2,
              department: 'Customer Service',
              maxConcurrentTasks: 3,
            },
          },
          {
            id: '4',
            type: 'agentNode',
            position: { x: 250, y: 350 },
            data: {
              name: 'Escalation Manager',
              role: 'supervisor' as const,
              skills: ['Conflict Resolution', 'Process Management', 'Customer Relations'],
              tools: [],
              description: 'Manages escalated issues and customer complaints',
              status: 'active' as const,
              level: 1,
              department: 'Customer Service',
              maxConcurrentTasks: 8,
            },
          }
        );
        break;

      case 'data-analytics':
        agents.push(
          {
            id: '1',
            type: 'agentNode',
            position: { x: 50, y: 100 },
            data: {
              name: 'Data Ingestion Agent',
              role: 'executor' as const,
              skills: ['API Integration', 'File Processing', 'Data Validation'],
              tools: [],
              description: 'Collects data from various sources',
              status: 'active' as const,
              level: 2,
              department: 'Data Engineering',
              maxConcurrentTasks: 10,
            },
          },
          {
            id: '2',
            type: 'agentNode',
            position: { x: 250, y: 100 },
            data: {
              name: 'ETL Processor',
              role: 'specialist' as const,
              skills: ['Data Transformation', 'Schema Mapping', 'Data Cleansing'],
              tools: [],
              description: 'Transforms and cleanses incoming data',
              status: 'active' as const,
              level: 2,
              department: 'Data Engineering',
              maxConcurrentTasks: 5,
            },
          },
          {
            id: '3',
            type: 'agentNode',
            position: { x: 450, y: 100 },
            data: {
              name: 'Quality Controller',
              role: 'specialist' as const,
              skills: ['Data Quality Assessment', 'Anomaly Detection', 'Validation Rules'],
              tools: [],
              description: 'Ensures data quality and integrity',
              status: 'active' as const,
              level: 2,
              department: 'Data Quality',
              maxConcurrentTasks: 3,
            },
          },
          {
            id: '4',
            type: 'agentNode',
            position: { x: 250, y: 250 },
            data: {
              name: 'Analytics Engine',
              role: 'specialist' as const,
              skills: ['Statistical Analysis', 'Machine Learning', 'Reporting'],
              tools: [],
              description: 'Performs analytics and generates insights',
              status: 'active' as const,
              level: 2,
              department: 'Analytics',
              maxConcurrentTasks: 2,
            },
          },
          {
            id: '5',
            type: 'agentNode',
            position: { x: 150, y: 400 },
            data: {
              name: 'Pipeline Coordinator',
              role: 'coordinator' as const,
              skills: ['Workflow Orchestration', 'Resource Management', 'Monitoring'],
              tools: [],
              description: 'Coordinates the entire data pipeline',
              status: 'active' as const,
              level: 0,
              department: 'Data Engineering',
              maxConcurrentTasks: 20,
            },
          }
        );
        break;

      case 'development':
        agents.push(
          {
            id: '1',
            type: 'agentNode',
            position: { x: 250, y: 50 },
            data: {
              name: 'Development Coordinator',
              role: 'coordinator' as const,
              skills: ['Project Management', 'Task Assignment', 'Code Integration'],
              tools: [],
              description: 'Coordinates development tasks and assignments',
              status: 'active' as const,
              level: 0,
              department: 'Engineering',
              maxConcurrentTasks: 15,
            },
          },
          {
            id: '2',
            type: 'agentNode',
            position: { x: 100, y: 200 },
            data: {
              name: 'Code Reviewer',
              role: 'specialist' as const,
              skills: ['Code Analysis', 'Security Review', 'Best Practices'],
              tools: [],
              description: 'Reviews code for quality and security',
              status: 'active' as const,
              level: 2,
              department: 'Engineering',
              maxConcurrentTasks: 3,
            },
          },
          {
            id: '3',
            type: 'agentNode',
            position: { x: 400, y: 200 },
            data: {
              name: 'Test Automation Agent',
              role: 'executor' as const,
              skills: ['Test Execution', 'Bug Detection', 'Performance Testing'],
              tools: [],
              description: 'Executes automated tests and reports results',
              status: 'active' as const,
              level: 2,
              department: 'QA',
              maxConcurrentTasks: 5,
            },
          },
          {
            id: '4',
            type: 'agentNode',
            position: { x: 250, y: 350 },
            data: {
              name: 'Deployment Manager',
              role: 'supervisor' as const,
              skills: ['CI/CD Management', 'Environment Control', 'Release Planning'],
              tools: [],
              description: 'Manages deployments and release processes',
              status: 'active' as const,
              level: 1,
              department: 'DevOps',
              maxConcurrentTasks: 7,
            },
          }
        );
        break;

      case 'security':
        agents.push(
          {
            id: '1',
            type: 'agentNode',
            position: { x: 250, y: 50 },
            data: {
              name: 'Security Monitor',
              role: 'executor' as const,
              skills: ['Log Analysis', 'Anomaly Detection', 'Alert Generation'],
              tools: [],
              description: 'Continuously monitors for security threats',
              status: 'active' as const,
              level: 2,
              department: 'Security',
              maxConcurrentTasks: 20,
            },
          },
          {
            id: '2',
            type: 'agentNode',
            position: { x: 100, y: 200 },
            data: {
              name: 'Incident Responder',
              role: 'specialist' as const,
              skills: ['Incident Analysis', 'Threat Hunting', 'Containment'],
              tools: [],
              description: 'Responds to and investigates security incidents',
              status: 'active' as const,
              level: 2,
              department: 'Security',
              maxConcurrentTasks: 3,
            },
          },
          {
            id: '3',
            type: 'agentNode',
            position: { x: 400, y: 200 },
            data: {
              name: 'Threat Intelligence Analyst',
              role: 'specialist' as const,
              skills: ['Threat Intelligence', 'IOC Analysis', 'Attribution'],
              tools: [],
              description: 'Analyzes threats and provides intelligence',
              status: 'active' as const,
              level: 2,
              department: 'Security',
              maxConcurrentTasks: 2,
            },
          },
          {
            id: '4',
            type: 'agentNode',
            position: { x: 250, y: 350 },
            data: {
              name: 'Security Coordinator',
              role: 'coordinator' as const,
              skills: ['Incident Coordination', 'Communication', 'Escalation'],
              tools: [],
              description: 'Coordinates security response activities',
              status: 'active' as const,
              level: 0,
              department: 'Security',
              maxConcurrentTasks: 10,
            },
          }
        );
        break;

      default:
        // Create a generic template
        agents.push(...createDefaultAgentNetwork());
    }

    return agents;
  };

  // Helper function to create edges between agents in a template
  const createAgentEdgesFromTemplate = (template: AgentTemplate, agents: Node[]): Edge[] => {
    const edges: Edge[] = [];
    const category = template.category.toLowerCase();

    // Create edges based on template category
    switch (category) {
      case 'customer-service':
        edges.push(
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
          }
        );
        break;

      case 'data-analytics':
        edges.push(
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
          }
        );
        break;

      case 'development':
        edges.push(
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
          }
        );
        break;

      case 'security':
        edges.push(
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
          }
        );
        break;
    }

    return edges;
  };

  // Helper function to create a default agent network
  const createDefaultAgentNetwork = (): Node[] => {
    return [
      {
        id: '1',
        type: 'agentNode',
        position: { x: 250, y: 100 },
        data: {
          name: 'Task Coordinator',
          role: 'coordinator' as const,
          skills: ['Task Management', 'Workflow Orchestration'],
          tools: [],
          description: 'Coordinates tasks and manages workflow execution',
          status: 'active' as const,
          level: 0,
          department: 'Operations',
          maxConcurrentTasks: 20,
        },
      },
      {
        id: '2',
        type: 'agentNode',
        position: { x: 150, y: 250 },
        data: {
          name: 'Data Processor',
          role: 'specialist' as const,
          skills: ['Data Processing', 'Analytics'],
          tools: [],
          description: 'Specializes in data processing and analysis tasks',
          status: 'active' as const,
          level: 2,
          department: 'Data',
          maxConcurrentTasks: 5,
        },
      },
      {
        id: '3',
        type: 'agentNode',
        position: { x: 350, y: 250 },
        data: {
          name: 'Communication Handler',
          role: 'specialist' as const,
          skills: ['Email Processing', 'Notifications'],
          tools: [],
          description: 'Handles all communication and notification tasks',
          status: 'active' as const,
          level: 2,
          department: 'Communications',
          maxConcurrentTasks: 10,
        },
      },
    ];
  };

  return (
    <div className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gray-50"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls className="bg-white border border-gray-200 rounded-lg" />
        <MiniMap
          className="bg-white border border-gray-200 rounded-lg"
          nodeColor="#8b5cf6"
          maskColor="rgba(0, 0, 0, 0.2)"
        />
        
        {/* Toolbar */}
        <Panel position="top-left">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-2">
            <div className="flex items-center space-x-2">
              <button
                onClick={addNewAgent}
                className="flex items-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Add Agent</span>
              </button>
              
              <button
                onClick={showSaveAgentDialog}
                className="flex items-center space-x-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              
              <button
                onClick={showLoadDialog}
                className="flex items-center space-x-1 px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors text-sm"
              >
                <Upload className="w-4 h-4" />
                <span>Load</span>
              </button>
              
              <button
                onClick={clearCanvas}
                className="flex items-center space-x-1 px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors text-sm"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear</span>
              </button>
            </div>
          </div>
        </Panel>
        
        {/* Agent Properties and Stats Panels */}
        <Panel position="top-right">
          <div className="space-y-2">
            {/* Agent Properties Panel */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[180px]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-gray-900 truncate" title={agentMetadata.name}>
                    {agentMetadata.name}
                  </h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded mt-1 inline-block">
                    {agentMetadata.category}
                  </span>
                </div>
                <button
                  onClick={handlePropertiesEdit}
                  className="ml-1 p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  title="Edit agent properties"
                >
                  <Settings className="h-3 w-3" />
                </button>
              </div>
              <div className="flex justify-between text-xs text-gray-600">
                <span>{agentMetadata.agentCount} agents</span>
                <span>{agentMetadata.connectionCount} connections</span>
              </div>
            </div>

            {/* Network Stats Panel */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-[180px]">
              <h3 className="font-semibold text-sm text-gray-900 mb-3 flex items-center">
                <Users className="w-4 h-4 mr-2" />
                Network Status
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Agents:</span>
                  <span className="font-medium">{nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Connections:</span>
                  <span className="font-medium">{edges.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Active:</span>
                  <span className="font-medium text-green-600">
                    {nodes.filter(n => n.data?.status === 'active').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Offline:</span>
                  <span className="font-medium text-gray-500">
                    {nodes.filter(n => n.data?.status === 'offline').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
      
      {/* Canvas Update Notification */}
      {canvasUpdateNotification?.show && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-purple-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-3 animate-fade-in">
            <CheckCircle2 className="w-5 h-5" />
            <div>
              <p className="font-medium">Agent Canvas Updated</p>
              <p className="text-sm opacity-90">{canvasUpdateNotification.message}</p>
            </div>
            <button
              onClick={() => setCanvasUpdateNotification(null)}
              className="ml-4 text-white hover:bg-purple-600 rounded p-1"
            >
              ×
            </button>
          </div>
        </div>
      )}
      
      {/* Agent Property Drawer */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={handleDrawerClose}
        title={selectedAgent ? `Configure ${selectedAgent.data?.name || 'Agent'}` : 'Agent Properties'}
        size="xl"
      >
        <AgentPropertyForm
          agent={selectedAgent}
          onUpdate={handleAgentUpdate}
          onClose={handleDrawerClose}
        />
      </Drawer>

      {/* Template Loader Dialog */}
      {showTemplateLoader && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Load Agent Template</h3>
              <button
                onClick={() => setShowTemplateLoader(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">

              <div className="mb-4">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="flex-1">
                    <input
                      type="file"
                      accept=".json,.yaml,.yml"
                      onChange={handleFileLoad}
                      className="hidden"
                      id="template-file-input"
                    />
                    <label
                      htmlFor="template-file-input"
                      className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50"
                    >
                      <Upload className="w-4 h-4" />
                      <span>Load from File</span>
                    </label>
                  </div>
                  <div className="text-sm text-gray-500">or choose from templates below</div>
                </div>
              </div>

              {/* Agent Template List */}
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-fuschia-500"></div>
                    <span className="text-gray-600">Loading agent templates from database...</span>
                  </div>
                </div>
              ) : availableTemplates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  {databaseConnectionError ? (
                    <>
                      <p className="text-red-600 font-medium">Database Connection Error</p>
                      <p className="text-sm text-red-500 mt-2">{databaseConnectionError}</p>
                      <p className="text-sm text-gray-500 mt-4">Please ensure the backend server is running and try again.</p>
                      <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 text-sm"
                      >
                        Retry Connection
                      </button>
                    </>
                  ) : (
                    <>
                      <p>No agent templates available</p>
                      <p className="text-sm">Create and save a template to see it here</p>
                    </>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {availableTemplates.map((template) => {
                    const complexityColors = {
                      simple: 'bg-green-100 text-green-800',
                      medium: 'bg-yellow-100 text-yellow-800', 
                      complex: 'bg-red-100 text-red-800',
                    };

                    const categoryIcons: Record<string, React.ReactNode> = {
                      'customer-service': '🎧',
                      'data-analytics': '📊', 
                      'development': '💻',
                      'security': '🛡️',
                      'enterprise': '🏢'
                    };

                    return (
                      <div
                        key={template.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white hover:border-fuschia-300"
                        onClick={() => loadAgentTemplate(template)}
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{categoryIcons[template.category] || '🤖'}</span>
                            <h4 className="font-semibold text-gray-900">{template.name}</h4>
                          </div>
                          <span className={`px-2 py-1 text-xs font-medium rounded ${complexityColors[template.complexity?.toLowerCase() as keyof typeof complexityColors] || complexityColors.simple}`}>
                            {template.complexity}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{template.description}</p>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                          <span>{template.agentCount} agents</span>
                          <span className="capitalize">{template.category.replace('-', ' ')}</span>
                        </div>

                        <div className="mb-3">
                          <h5 className="text-xs font-medium text-gray-700 mb-1">Features:</h5>
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

                        <div className="pt-2 border-t border-gray-100">
                          <p className="text-xs text-gray-600 font-medium">{template.useCase}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowTemplateLoader(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save Template Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                {currentTemplateId ? 'Update Agent Template' : 'Save Agent Template'}
              </h3>
            </div>
            
            <div className="px-6 py-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={saveFormData.name}
                    onChange={(e) => setSaveFormData({ ...saveFormData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    placeholder="Enter template name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={saveFormData.description}
                    onChange={(e) => setSaveFormData({ ...saveFormData, description: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                    rows={3}
                    placeholder="Describe what this agent organization does"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={saveFormData.category}
                    onChange={(e) => setSaveFormData({ ...saveFormData, category: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  >
                    <option value="Custom">Custom</option>
                    <option value="customer-service">Customer Service</option>
                    <option value="data-analytics">Data Analytics</option>
                    <option value="development">Development</option>
                    <option value="security">Security</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>
                
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <label className="block text-sm font-medium text-gray-700">
                      Save Location
                    </label>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-md p-3">
                    <p className="text-sm text-green-800">
                      <strong>Database</strong> - Agent template will be saved to the database for team access and collaboration (with local storage fallback).
                    </p>
                  </div>
                  
                  <div className="mt-3">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={!!saveFormData.folder}
                        onChange={(e) => setSaveFormData({ 
                          ...saveFormData, 
                          folder: e.target.checked ? 'download' : '' 
                        })}
                        className="rounded border-gray-300 text-fuschia-600 focus:ring-fuschia-500"
                      />
                      <span className="text-sm text-gray-700">Also download as backup file</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowSaveDialog(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={saveAgentAsTemplate}
                className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
              >
                {currentTemplateId ? 'Update Template' : 'Save Template'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Agent Organization Properties Drawer */}
      <Drawer 
        isOpen={isPropertiesDialogOpen} 
        onClose={handlePropertiesCancel}
        title="Agent Organization Properties"
        size="xl"
      >
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Name
            </label>
            <input
              type="text"
              value={agentMetadata.name}
              onChange={(e) => setAgentMetadata({ ...agentMetadata, name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              placeholder="Enter agent organization name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select 
              value={agentMetadata.category} 
              onChange={(e) => setAgentMetadata({ ...agentMetadata, category: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              <option value="Custom">Custom</option>
              <option value="customer-service">Customer Service</option>
              <option value="data-analytics">Data Analytics</option>
              <option value="development">Development</option>
              <option value="security">Security</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea 
              value={agentMetadata.description} 
              onChange={(e) => setAgentMetadata({ ...agentMetadata, description: e.target.value })}
              rows={4}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              placeholder="Describe what this agent organization does and its purpose..."
            />
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Organization Statistics</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Agents:</span>
                <span className="ml-2 font-medium">{agentMetadata.agentCount}</span>
              </div>
              <div>
                <span className="text-gray-600">Connections:</span>
                <span className="ml-2 font-medium">{agentMetadata.connectionCount}</span>
              </div>
              <div>
                <span className="text-gray-600">Active Agents:</span>
                <span className="ml-2 font-medium text-green-600">
                  {nodes.filter(n => n.data?.status === 'active').length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Offline Agents:</span>
                <span className="ml-2 font-medium text-gray-500">
                  {nodes.filter(n => n.data?.status === 'offline').length}
                </span>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              onClick={handlePropertiesCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handlePropertiesSave}
              className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </Drawer>
    </div>
  );
};