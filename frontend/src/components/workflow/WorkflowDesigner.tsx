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
import { Plus, Play, Save, Download, Upload } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAppStore } from '@/store/appStore';
import { Drawer } from '@/components/ui/Drawer';
import { NodePropertyForm } from './NodePropertyForm';

// Define workflow step types
export interface WorkflowStepData {
  label: string;
  type: 'trigger' | 'action' | 'condition' | 'end';
  description: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  app?: string;
  action?: string;
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

  const getStatusIndicator = () => {
    switch (data.status) {
      case 'running':
        return <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />;
      case 'completed':
        return <div className="w-2 h-2 bg-green-500 rounded-full" />;
      case 'error':
        return <div className="w-2 h-2 bg-red-500 rounded-full" />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
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
          {getStatusIndicator()}
          <span className="text-xs font-semibold uppercase tracking-wide">
            {data.type}
          </span>
        </div>
      </div>
      
      <div className="font-medium text-sm mb-1">{data.label}</div>
      
      {data.app && (
        <div className="text-xs text-gray-600 mb-1">
          {data.app} • {data.action}
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
      status: 'idle',
      app: 'Webhook',
      action: 'Receive POST request',
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
      status: 'idle',
      app: 'Data Processor',
      action: 'Validate fields',
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
      status: 'idle',
      app: 'Email',
      action: 'Send email',
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
  
  // Update nodes and edges when workflowData changes
  useEffect(() => {
    if (workflowData) {
      setNodes(workflowData.nodes);
      setEdges(workflowData.edges);
    }
  }, [workflowData, setNodes, setEdges]);

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
        status: 'idle',
        app: 'Select app',
        action: 'Select action',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, setNodes]);

  const runWorkflow = useCallback(async () => {
    setIsRunning(true);
    
    // Simulate workflow execution
    for (let i = 0; i < nodes.length; i++) {
      const nodeId = nodes[i].id;
      
      // Set node as running
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, status: 'running' } }
            : node
        )
      );
      
      // Wait 1 second
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Set node as completed
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, status: 'completed' } }
            : node
        )
      );
    }
    
    setIsRunning(false);
  }, [nodes, setNodes]);

  const saveWorkflow = useCallback(() => {
    const workflow = {
      nodes,
      edges,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(workflow, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'workflow.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [nodes, edges]);

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
                onClick={saveWorkflow}
                className="flex items-center space-x-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              
              <button
                onClick={saveWorkflow}
                className="flex items-center space-x-1 px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </Panel>
        
        {/* Status Panel */}
        <Panel position="top-right">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-[200px]">
            <h3 className="font-semibold text-sm text-gray-900 mb-3">Workflow Status</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Steps:</span>
                <span className="font-medium">{nodes.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Connections:</span>
                <span className="font-medium">{edges.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={cn(
                  "font-medium",
                  isRunning ? "text-blue-600" : "text-green-600"
                )}>
                  {isRunning ? 'Running' : 'Ready'}
                </span>
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
    </div>
  );
};