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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Plus, Play, Save, Upload, FolderOpen, Trash2, Settings } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAppStore } from '@/store/appStore';
import { Drawer } from '@/components/ui/Drawer';
import { NodePropertyForm } from './NodePropertyForm';
import { templateService, WorkflowTemplate } from '@/services/templateService';
import { workflowService } from '@/services/workflowService';
import { workflowExecutionService } from '@/services/workflowExecutionService';

// Define workflow step types
export interface WorkflowStepData {
  label: string;
  type: 'trigger' | 'action' | 'condition' | 'end';
  description: string;
  objective?: string;
  completionCriteria?: string;
}

// Custom node component
const WorkflowStepNode: React.FC<{ data: WorkflowStepData; selected: boolean }> = ({ data, selected }) => {
  const getNodeColor = () => {
    switch (data.type) {
      case 'trigger':
        return 'bg-green-100 border-green-300 text-green-800';
      case 'action':
        return 'bg-blue-100 border-blue-300 text-blue-800';
      case 'condition':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'end':
        return 'bg-red-100 border-red-300 text-red-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const getTypeIcon = () => {
    switch (data.type) {
      case 'trigger':
        return '▶️';
      case 'action':
        return '⚡';
      case 'condition':
        return '❓';
      case 'end':
        return '🏁';
      default:
        return '📋';
    }
  };

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[200px] shadow-sm relative',
        getNodeColor(),
        selected && 'ring-2 ring-fuschia-500'
      )}
    >
      {/* Input Handle - only show if not a trigger node */}
      {data.type !== 'trigger' && (
        <Handle
          type="target"
          position={Position.Top}
          className="!bg-gray-500 !border-2 !border-white !w-3 !h-3"
        />
      )}
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm">{getTypeIcon()}</span>
          <span className="text-xs font-semibold uppercase tracking-wide">
            {data.type}
          </span>
        </div>
      </div>
      
      <div className="font-medium text-sm mb-1">{data.label}</div>
      
      {data.objective && (
        <div className="text-xs text-gray-600 mb-1">
          <span className="font-medium">Objective:</span> {data.objective.length > 40 ? `${data.objective.substring(0, 40)}...` : data.objective}
        </div>
      )}
      
      {data.completionCriteria && (
        <div className="text-xs text-gray-500 mb-1">
          <span className="font-medium">Success:</span> {data.completionCriteria.length > 35 ? `${data.completionCriteria.substring(0, 35)}...` : data.completionCriteria}
        </div>
      )}
      
      {data.description && (
        <div className="text-xs text-gray-500 leading-tight">
          {data.description}
        </div>
      )}
      
      {/* Output Handle - only show if not an end node */}
      {data.type !== 'end' && (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!bg-gray-500 !border-2 !border-white !w-3 !h-3"
        />
      )}
    </div>
  );
};

// Node types
const nodeTypes = {
  workflowStep: WorkflowStepNode,
};

// Initial nodes
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'workflowStep',
    position: { x: 100, y: 100 },
    data: {
      label: 'When form submitted',
      type: 'trigger',
      description: 'Triggers when a new form is submitted',
      objective: 'Capture incoming form data and initiate workflow',
      completionCriteria: 'Form data received and parsed successfully',
    },
  },
  {
    id: '2',
    type: 'workflowStep',
    position: { x: 100, y: 250 },
    data: {
      label: 'Validate data',
      type: 'condition',
      description: 'Check if all required fields are present',
      objective: 'Ensure data integrity and completeness',
      completionCriteria: 'All required fields validated and data format confirmed',
    },
  },
  {
    id: '3',
    type: 'workflowStep',
    position: { x: 100, y: 400 },
    data: {
      label: 'Send notification',
      type: 'action',
      description: 'Send email notification to admin',
      objective: 'Notify stakeholders of successful form submission',
      completionCriteria: 'Email delivered successfully with confirmation receipt',
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
    style: { stroke: '#6366f1', strokeWidth: 2 },
  },
  {
    id: 'e2-3',
    source: '2',
    target: '3',
    type: 'smoothstep',
    style: { stroke: '#6366f1', strokeWidth: 2 },
  },
];

interface WorkflowDesignerProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
}

export const WorkflowDesigner: React.FC<WorkflowDesignerProps> = ({ 
  initialNodes: propInitialNodes, 
  initialEdges: propInitialEdges
}) => {
  const { workflowData } = useAppStore();
  
  // Use prop nodes/edges if provided, otherwise use workflow data from store, otherwise use default
  const defaultNodes = propInitialNodes || (workflowData?.nodes) || initialNodes;
  const defaultEdges = propInitialEdges || (workflowData?.edges) || initialEdges;
  
  const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(defaultEdges);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showTemplateLoader, setShowTemplateLoader] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [availableTemplates, setAvailableTemplates] = useState<WorkflowTemplate[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [saveFormData, setSaveFormData] = useState({
    name: '',
    description: '',
    category: 'Custom',
    folder: '',
  });
  
  // Workflow metadata state
  const [workflowMetadata, setWorkflowMetadata] = useState({
    name: 'Untitled Workflow',
    description: 'Describe what this workflow does...',
    category: 'Custom',
  });
  
  // State for properties dialog
  const [isPropertiesDialogOpen, setIsPropertiesDialogOpen] = useState(false);
  
  // Update nodes and edges when workflowData changes
  useEffect(() => {
    if (workflowData) {
      setNodes(workflowData.nodes);
      setEdges(workflowData.edges);
      
      // Update metadata if available
      if (workflowData.metadata) {
        setWorkflowMetadata({
          name: workflowData.metadata.name || 'Untitled Workflow',
          description: workflowData.metadata.description || 'Describe what this workflow does...',
          category: workflowData.metadata.category || 'Custom',
        });
      }
    }
  }, [workflowData, setNodes, setEdges]);

  // Load available templates and categories from database
  useEffect(() => {
    const loadTemplatesFromDatabase = async () => {
      try {
        // Test database connection first
        const isConnected = await workflowService.testConnection();
        if (isConnected) {
          console.log('Loading workflow templates from database...');
          const databaseTemplates = await workflowService.getWorkflowTemplatesFromDatabase();
          console.log('Loaded templates from database:', databaseTemplates);
          setAvailableTemplates(databaseTemplates);
          
          // Extract categories from database templates
          const dbCategories = [...new Set(databaseTemplates.map(t => t.category))];
          setAvailableCategories(['Custom', ...dbCategories]);
        } else {
          console.warn('Database not available, falling back to local storage templates');
          // Fallback to local storage if database is not available
          setAvailableTemplates(templateService.getAllTemplates());
          setAvailableCategories(['Custom', 'Fuschia', ...templateService.getAvailableCategories()]);
        }
      } catch (error) {
        console.error('Failed to load templates from database:', error);
        // Fallback to local storage on error
        setAvailableTemplates(templateService.getAllTemplates());
        setAvailableCategories(['Custom', 'Fuschia', ...templateService.getAvailableCategories()]);
      }
    };

    loadTemplatesFromDatabase();
  }, []);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setIsDrawerOpen(true);
  }, []);

  const handleNodeUpdate = useCallback((nodeId: string, newData: Partial<WorkflowStepData>) => {
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
    setSelectedNode(null);
  }, []);

  const addNewNode = useCallback(() => {
    const newNode: Node = {
      id: `${nodes.length + 1}`,
      type: 'workflowStep',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        label: 'New step',
        type: 'action',
        description: 'Configure this step',
        objective: 'Define what this step should accomplish',
        completionCriteria: 'Define success criteria for this step',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, setNodes]);

  const runWorkflow = useCallback(async () => {
    if (nodes.length === 0) {
      alert('Cannot run empty workflow. Please add some workflow steps first.');
      return;
    }

    setIsRunning(true);
    
    try {
      // First save the workflow as a template if it's not already saved
      let templateId = '';
      
      // Check if this workflow has been saved before
      const workflowData = useAppStore.getState().workflowData;
      if (workflowData?.metadata?.savedId) {
        templateId = workflowData.metadata.savedId;
      } else {
        // Save as temporary template for execution
        const tempTemplate = {
          name: workflowMetadata.name || `Execution ${new Date().toLocaleString()}`,
          description: workflowMetadata.description || 'Temporary workflow for execution',
          category: workflowMetadata.category || 'Execution',
          complexity: 'medium' as const,
          estimatedTime: '30-60 minutes',
          tags: ['execution', 'temporary'],
          nodes: nodes.map(node => ({ ...node, selected: false, dragging: false })),
          edges: edges.map(edge => ({ ...edge, selected: false })),
        };

        const savedTemplate = await workflowService.saveWorkflowToDatabase(tempTemplate);
        templateId = savedTemplate.id;
      }

      // Execute the workflow
      console.log('Starting workflow execution for template:', templateId);
      const execution = await workflowExecutionService.executeWorkflow(templateId, {
        execution_context: {
          executed_from: 'designer',
          node_count: nodes.length,
          edge_count: edges.length,
          initiated_at: new Date().toISOString()
        },
        priority: 1
      });

      console.log('Workflow execution started:', execution);
      
      // Show success message with execution details
      const executionUrl = `/executions/${execution.id}`;
      const message = `Workflow execution started successfully!\n\nExecution ID: ${execution.id}\nStatus: ${execution.status}\nTasks: ${execution.tasks.length}\n\nYou can monitor the execution progress in the Workflow Executions section.`;
      
      alert(message);
      
      // Optionally redirect to execution view
      // window.location.href = executionUrl;
      
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      alert(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsRunning(false);
    }
  }, [nodes, edges, workflowMetadata]);

  const showSaveWorkflowDialog = useCallback(() => {
    // Initialize form with current workflow metadata
    setSaveFormData({
      name: workflowMetadata.name !== 'Untitled Workflow' ? workflowMetadata.name : `Workflow ${new Date().toLocaleDateString()}`,
      description: workflowMetadata.description !== 'Describe what this workflow does...' ? workflowMetadata.description : 'Custom workflow created in designer',
      category: workflowMetadata.category || 'Custom',
      folder: templateService.getTemplateSettings().customTemplatesFolder,
    });
    setShowSaveDialog(true);
  }, [workflowMetadata]);

  const saveWorkflowAsTemplate = useCallback(async () => {
    if (!saveFormData.name.trim()) {
      alert('Please enter a name for the template');
      return;
    }

    try {
      // Check database connectivity first
      const isConnected = await workflowService.testConnection();
      if (!isConnected) {
        throw new Error('Database connection failed. Please check if the backend is running.');
      }

      // Determine complexity based on node count and edge complexity
      let complexity = 'simple';
      if (nodes.length > 5 || edges.length > 7) {
        complexity = 'medium';
      }
      if (nodes.length > 10 || edges.length > 15) {
        complexity = 'advanced';
      }

      // Extract preview steps from nodes
      const previewSteps = nodes
        .slice(0, 5)
        .map(node => String(node.data?.label || 'Unnamed step'))
        .filter(step => step.trim().length > 0);

      // Estimate time based on complexity
      const estimatedTime = complexity === 'simple' ? '15-30 minutes' : 
                           complexity === 'medium' ? '1-2 hours' : 
                           '2+ hours';

      // Prepare workflow data for PostgreSQL
      const workflowData = {
        name: saveFormData.name,
        description: saveFormData.description,
        category: saveFormData.category,
        complexity,
        estimatedTime,
        tags: [saveFormData.category, 'Custom', workflowMetadata.name !== 'Untitled Workflow' ? 'Named' : 'Untitled'],
        nodes: nodes.map(node => ({
          ...node,
          selected: false,
          dragging: false,
        })),
        edges: edges.map(edge => ({
          ...edge,
          selected: false,
        })),
      };

      // Save to PostgreSQL database
      const savedWorkflow = await workflowService.saveWorkflowToDatabase(workflowData);

      // Update workflow metadata to reflect saved state
      setWorkflowMetadata({
        name: savedWorkflow.name,
        description: savedWorkflow.description,
        category: saveFormData.category,
      });

      // Update the workflow data in the store with saved metadata
      const { setWorkflowData } = useAppStore.getState();
      const currentWorkflowData = useAppStore.getState().workflowData;
      
      if (currentWorkflowData) {
        setWorkflowData({
          ...currentWorkflowData,
          metadata: {
            ...currentWorkflowData.metadata,
            name: savedWorkflow.name,
            description: savedWorkflow.description,
            category: saveFormData.category,
            savedId: savedWorkflow.id,
            savedAt: savedWorkflow.created_at,
          }
        });
      }

      // Also save as local template for backward compatibility (optional)
      if (saveFormData.folder.trim()) {
        const template = templateService.createTemplateFromWorkflow(
          saveFormData.name,
          saveFormData.description,
          saveFormData.category,
          nodes,
          edges
        );
        templateService.saveTemplateToFile(template);
      }

      // Update available templates from database
      try {
        const databaseTemplates = await workflowService.getWorkflowTemplatesFromDatabase();
        setAvailableTemplates(databaseTemplates);
      } catch (error) {
        console.error('Failed to refresh templates from database:', error);
        // Fallback to local storage if database refresh fails
        setAvailableTemplates(templateService.getAllTemplates());
      }

      // Close dialog and show success
      setShowSaveDialog(false);
      alert(`Workflow "${savedWorkflow.name}" saved successfully to database!\nID: ${savedWorkflow.id}`);
      
      // Reset form
      setSaveFormData({
        name: '',
        description: '',
        category: 'Custom',
        folder: '',
      });

    } catch (error) {
      console.error('Failed to save workflow:', error);
      
      // Fallback to local save if database fails
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const shouldFallback = confirm(
        `Failed to save to database: ${errorMessage}\n\nWould you like to save locally instead?`
      );
      
      if (shouldFallback) {
        try {
          const template = templateService.createTemplateFromWorkflow(
            saveFormData.name,
            saveFormData.description,
            saveFormData.category,
            nodes,
            edges
          );
          templateService.saveCustomTemplate(template);
          
          if (saveFormData.folder.trim()) {
            templateService.saveTemplateToFile(template);
          }
          
          setAvailableTemplates(templateService.getAllTemplates());
          setShowSaveDialog(false);
          alert(`Template "${saveFormData.name}" saved locally as fallback.`);
          
          setSaveFormData({
            name: '',
            description: '',
            category: 'Custom',
            folder: '',
          });
        } catch (fallbackError) {
          alert(`Both database and local save failed: ${fallbackError instanceof Error ? fallbackError.message : 'Unknown error'}`);
        }
      }
    }
  }, [saveFormData, nodes, edges, workflowMetadata]);

  const loadTemplate = useCallback((template: WorkflowTemplate) => {
    console.log('Loading template:', template.name, `(${template.nodes?.length || 0} nodes, ${template.edges?.length || 0} edges)`);
    
    // Clear existing canvas first
    setNodes([]);
    setEdges([]);
    
    // Update metadata
    setWorkflowMetadata({
      name: template.name,
      description: template.description,
      category: template.category || 'Custom',
    });
    
    // Validate and process nodes and edges
    const processedNodes = (template.nodes || []).map((node, index) => {
      // Ensure each node has required ReactFlow properties
      return {
        id: node.id || `node-${index}`,
        type: node.type || 'workflowStep',
        position: node.position || { x: 100 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 200 },
        data: node.data || {
          label: 'Unnamed Step',
          type: 'action',
          description: 'Configure this step',
          objective: 'Define what this step should accomplish',
          completionCriteria: 'Define success criteria for this step',
        },
        selected: false,
        dragging: false
      };
    });
    
    const processedEdges = (template.edges || []).map((edge, index) => {
      // Ensure each edge has required ReactFlow properties
      return {
        id: edge.id || `edge-${index}`,
        source: edge.source,
        target: edge.target,
        type: edge.type || 'smoothstep',
        style: edge.style || { stroke: '#6366f1', strokeWidth: 2 },
        selected: false
      };
    });
    
    if (processedNodes.length === 0 && processedEdges.length === 0) {
      console.warn('Template has no nodes or edges - template data may be empty');
    }
    
    // Small delay to ensure clearing is visible
    setTimeout(() => {
      setNodes(processedNodes);
      setEdges(processedEdges);
    }, 100);
    
    setShowTemplateLoader(false);
  }, [setNodes, setEdges]);

  const handleFileLoad = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const template = await templateService.loadTemplateFromFile(file);
      loadTemplate(template);
    } catch (error) {
      alert(`Failed to load template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    
    // Reset file input
    event.target.value = '';
  }, [loadTemplate]);

  const showLoadDialog = useCallback(() => {
    setShowTemplateLoader(true);
  }, []);

  const clearCanvas = useCallback(() => {
    if (nodes.length === 0 && edges.length === 0) {
      return; // Canvas is already empty
    }
    
    if (confirm('Are you sure you want to clear the canvas? This will remove all nodes and edges.')) {
      setNodes([]);
      setEdges([]);
      setWorkflowMetadata({
        name: 'Untitled Workflow',
        description: 'Describe what this workflow does...',
        category: 'Custom',
      });
    }
  }, [nodes.length, edges.length, setNodes, setEdges]);

  const handlePropertiesEdit = useCallback(() => {
    setIsPropertiesDialogOpen(true);
  }, []);

  const handlePropertiesSave = useCallback(() => {
    setIsPropertiesDialogOpen(false);
    
    // Update the workflow data in the store with new metadata
    const { setWorkflowData } = useAppStore.getState();
    const currentWorkflowData = useAppStore.getState().workflowData;
    
    if (currentWorkflowData) {
      setWorkflowData({
        ...currentWorkflowData,
        metadata: {
          ...currentWorkflowData.metadata,
          name: workflowMetadata.name,
          description: workflowMetadata.description,
          category: workflowMetadata.category,
        }
      });
    }
  }, [workflowMetadata]);

  const handlePropertiesCancel = useCallback(() => {
    setIsPropertiesDialogOpen(false);
    
    // Reset to original values from store
    const currentWorkflowData = useAppStore.getState().workflowData;
    if (currentWorkflowData?.metadata) {
      setWorkflowMetadata({
        name: currentWorkflowData.metadata.name || 'Untitled Workflow',
        description: currentWorkflowData.metadata.description || 'Describe what this workflow does...',
        category: currentWorkflowData.metadata.category || 'Custom',
      });
    }
  }, []);

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
          nodeColor="#d946ef"
          maskColor="rgba(0, 0, 0, 0.2)"
        />
        
        {/* Toolbar */}
        <Panel position="top-left">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-2">
            <div className="flex items-center space-x-2">
              <button
                onClick={addNewNode}
                className="flex items-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors text-sm"
              >
                <Plus className="w-4 h-4" />
                <span>Add Step</span>
              </button>
              
              <button
                onClick={runWorkflow}
                disabled={isRunning}
                className="flex items-center space-x-1 px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                <Play className="w-4 h-4" />
                <span>{isRunning ? 'Running...' : 'Run'}</span>
              </button>
              
              <button
                onClick={showSaveWorkflowDialog}
                className="flex items-center space-x-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              
              <button
                onClick={showLoadDialog}
                className="flex items-center space-x-1 px-3 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors text-sm"
              >
                <FolderOpen className="w-4 h-4" />
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

        {/* Stacked Info & Status Panels - Top Right */}
        <Panel position="top-right">
          <div className="space-y-2">
            {/* Minimized Workflow Info Panel */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[180px]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-gray-900 truncate">
                    {workflowMetadata.name}
                  </h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded mt-1 inline-block">
                    {workflowMetadata.category}
                  </span>
                </div>
                <button
                  onClick={handlePropertiesEdit}
                  className="ml-1 p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
                  title="Edit workflow properties"
                >
                  <Settings className="h-3 w-3" />
                </button>
              </div>
              
              {/* Compact workflow stats */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Steps:</span>
                  <span className="font-medium">{nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Links:</span>
                  <span className="font-medium">{edges.length}</span>
                </div>
              </div>
            </div>

            {/* Status Panel */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 min-w-[180px]">
              <div className="space-y-2">
                {/* Status indicator */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Status</span>
                  <span className={cn(
                    "px-2 py-1 rounded text-xs font-medium",
                    isRunning 
                      ? "bg-blue-100 text-blue-700" 
                      : "bg-green-100 text-green-700"
                  )}>
                    {isRunning ? 'Running' : 'Ready'}
                  </span>
                </div>
                
                {/* Save status */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Saved</span>
                  <div className="flex items-center space-x-1">
                    {workflowData?.metadata?.savedId ? (
                      <>
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-xs text-green-600 font-medium">Yes</span>
                      </>
                    ) : (
                      <>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <span className="text-xs text-gray-500">No</span>
                      </>
                    )}
                  </div>
                </div>
                
                {workflowData?.metadata?.savedId && (
                  <div className="text-xs text-gray-500 truncate border-t border-gray-100 pt-2 mt-2">
                    ID: {workflowData.metadata.savedId.split('-')[0]}...
                  </div>
                )}
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
      
      {/* Node Property Drawer */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={handleDrawerClose}
        title={selectedNode ? `Edit ${selectedNode.data?.label || 'Node'}` : 'Node Properties'}
        size="md"
      >
        <NodePropertyForm
          node={selectedNode}
          onUpdate={handleNodeUpdate}
          onClose={handleDrawerClose}
        />
      </Drawer>

      {/* Template Loader Dialog */}
      {showTemplateLoader && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Load Template</h3>
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

              {/* Template List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availableTemplates.map((template) => (
                  <div
                    key={template.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => loadTemplate(template)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">{template.name}</h4>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {template.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{template.steps} steps</span>
                      <span>{template.estimatedTime}</span>
                      <span className={`px-2 py-1 rounded ${
                        template.complexity === 'Simple' ? 'bg-green-100 text-green-800' :
                        template.complexity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {template.complexity}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {template.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
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
              <h3 className="text-lg font-medium text-gray-900">Save Template</h3>
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
                    placeholder="Describe what this template does"
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
                    {availableCategories.map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
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
                      <strong>PostgreSQL Database</strong> - Workflow will be saved to the database for team access and collaboration.
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
                onClick={saveWorkflowAsTemplate}
                className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
              >
                Save Template
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Properties Drawer */}
      <Drawer 
        isOpen={isPropertiesDialogOpen} 
        onClose={handlePropertiesCancel}
        title="Workflow Properties"
        size="lg"
      >
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Workflow Name
            </label>
            <input
              type="text"
              value={workflowMetadata.name}
              onChange={(e) => setWorkflowMetadata({ ...workflowMetadata, name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              placeholder="Enter workflow name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={workflowMetadata.category}
              onChange={(e) => setWorkflowMetadata({ ...workflowMetadata, category: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              {availableCategories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={workflowMetadata.description}
              onChange={(e) => setWorkflowMetadata({ ...workflowMetadata, description: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              rows={4}
              placeholder="Describe what this workflow does"
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              onClick={handlePropertiesCancel}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 text-sm"
            >
              Cancel
            </button>
            <button
              onClick={handlePropertiesSave}
              className="px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 text-sm"
            >
              Save Properties
            </button>
          </div>
        </div>
      </Drawer>
    </div>
  );
};