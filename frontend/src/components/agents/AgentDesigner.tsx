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
import { Plus, Users, Save, Download, Settings } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAppStore } from '@/store/appStore';
import { Drawer } from '@/components/ui/Drawer';
import { AgentPropertyForm } from './AgentPropertyForm';

// Define agent data types
export interface AgentData {
  name: string;
  role: 'supervisor' | 'specialist' | 'coordinator' | 'executor';
  skills: string[];
  tools: string[];
  description: string;
  status: 'active' | 'idle' | 'busy' | 'offline';
  level: number; // 0 = entry point, 1 = supervisor, 2 = specialist
  department?: string;
  maxConcurrentTasks?: number;
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

  // Update nodes and edges when agentData changes
  useEffect(() => {
    if (agentData?.nodes && agentData?.edges) {
      setNodes(agentData.nodes);
      setEdges(agentData.edges);
    }
  }, [agentData, setNodes, setEdges]);

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

  const saveAgentNetwork = useCallback(() => {
    const network = {
      agents: nodes,
      connections: edges,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(network, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agent-network.json';
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
                onClick={saveAgentNetwork}
                className="flex items-center space-x-1 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              
              <button
                onClick={saveAgentNetwork}
                className="flex items-center space-x-1 px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors text-sm"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </Panel>
        
        {/* Network Stats Panel */}
        <Panel position="top-right">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-[200px]">
            <h3 className="font-semibold text-sm text-gray-900 mb-3 flex items-center">
              <Users className="w-4 h-4 mr-2" />
              Agent Network
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
                  {nodes.filter(n => n.data.status === 'active').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Offline:</span>
                <span className="font-medium text-gray-500">
                  {nodes.filter(n => n.data.status === 'offline').length}
                </span>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
      
      {/* Agent Property Drawer */}
      <Drawer
        isOpen={isDrawerOpen}
        onClose={handleDrawerClose}
        title={selectedAgent ? `Configure ${selectedAgent.data?.name || 'Agent'}` : 'Agent Properties'}
        size="lg"
      >
        <AgentPropertyForm
          agent={selectedAgent}
          onUpdate={handleAgentUpdate}
          onClose={handleDrawerClose}
        />
      </Drawer>
    </div>
  );
};