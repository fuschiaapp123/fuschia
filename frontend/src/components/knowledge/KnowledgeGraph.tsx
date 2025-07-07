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
import { 
  Search, 
  Filter, 
  Layers, 
  RefreshCw,
  Database,
  User,
  Building,
  FileText,
  Settings,
  Zap
} from 'lucide-react';
import { cn } from '@/utils/cn';

// Define knowledge node types
export interface KnowledgeNodeData {
  label: string;
  type: 'entity' | 'process' | 'system' | 'document' | 'person' | 'department';
  properties: Record<string, any>;
  description: string;
  source?: string;
  lastUpdated?: string;
}

// Custom knowledge node component
const KnowledgeNode: React.FC<{ data: KnowledgeNodeData; selected: boolean }> = ({ data, selected }) => {
  const getNodeStyle = () => {
    switch (data.type) {
      case 'entity':
        return 'bg-blue-100 border-blue-300 text-blue-800';
      case 'process':
        return 'bg-green-100 border-green-300 text-green-800';
      case 'system':
        return 'bg-purple-100 border-purple-300 text-purple-800';
      case 'document':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'person':
        return 'bg-pink-100 border-pink-300 text-pink-800';
      case 'department':
        return 'bg-indigo-100 border-indigo-300 text-indigo-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const getNodeIcon = () => {
    switch (data.type) {
      case 'entity':
        return <Database className="w-4 h-4" />;
      case 'process':
        return <Zap className="w-4 h-4" />;
      case 'system':
        return <Settings className="w-4 h-4" />;
      case 'document':
        return <FileText className="w-4 h-4" />;
      case 'person':
        return <User className="w-4 h-4" />;
      case 'department':
        return <Building className="w-4 h-4" />;
      default:
        return <Database className="w-4 h-4" />;
    }
  };

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px] max-w-[220px] shadow-sm relative bg-white',
        getNodeStyle(),
        selected && 'ring-2 ring-fuschia-500'
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-500 !border-2 !border-white !w-3 !h-3"
      />
      
      <div className="flex items-center space-x-2 mb-2">
        {getNodeIcon()}
        <span className="text-xs font-semibold uppercase tracking-wide">
          {data.type}
        </span>
      </div>
      
      <div className="font-bold text-sm mb-1">{data.label}</div>
      
      {data.description && (
        <div className="text-xs text-gray-600 leading-tight">
          {data.description.substring(0, 80)}
          {data.description.length > 80 && '...'}
        </div>
      )}
      
      {data.source && (
        <div className="text-xs text-gray-500 mt-1">
          From: {data.source}
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-gray-500 !border-2 !border-white !w-3 !h-3"
      />
    </div>
  );
};

// Node types
const nodeTypes = {
  knowledgeNode: KnowledgeNode,
};

// Sample knowledge graph data
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'knowledgeNode',
    position: { x: 250, y: 50 },
    data: {
      label: 'Customer Service',
      type: 'department',
      description: 'Customer support and service operations department',
      properties: { employees: 25, location: 'Building A' },
      source: 'HR Database'
    },
  },
  {
    id: '2',
    type: 'knowledgeNode',
    position: { x: 100, y: 200 },
    data: {
      label: 'ServiceNow',
      type: 'system',
      description: 'IT Service Management platform for incident and change management',
      properties: { version: 'Paris', url: 'company.service-now.com' },
      source: 'ServiceNow API'
    },
  },
  {
    id: '3',
    type: 'knowledgeNode',
    position: { x: 400, y: 200 },
    data: {
      label: 'Salesforce',
      type: 'system',
      description: 'Customer relationship management platform',
      properties: { edition: 'Enterprise', users: 150 },
      source: 'Salesforce API'
    },
  },
  {
    id: '4',
    type: 'knowledgeNode',
    position: { x: 50, y: 350 },
    data: {
      label: 'Incident Management',
      type: 'process',
      description: 'Process for handling and resolving IT incidents',
      properties: { sla: '4 hours', priority_levels: 4 },
      source: 'ServiceNow'
    },
  },
  {
    id: '5',
    type: 'knowledgeNode',
    position: { x: 200, y: 350 },
    data: {
      label: 'Change Request',
      type: 'process',
      description: 'Process for managing changes to IT infrastructure',
      properties: { approval_required: true, risk_assessment: true },
      source: 'ServiceNow'
    },
  },
  {
    id: '6',
    type: 'knowledgeNode',
    position: { x: 350, y: 350 },
    data: {
      label: 'Customer Account',
      type: 'entity',
      description: 'Customer account information and details',
      properties: { total_accounts: 1245, active_accounts: 1156 },
      source: 'Salesforce'
    },
  },
  {
    id: '7',
    type: 'knowledgeNode',
    position: { x: 500, y: 350 },
    data: {
      label: 'Sales Opportunity',
      type: 'entity',
      description: 'Sales pipeline and opportunity tracking',
      properties: { total_value: '$2.5M', avg_deal_size: '$25K' },
      source: 'Salesforce'
    },
  },
  {
    id: '8',
    type: 'knowledgeNode',
    position: { x: 150, y: 500 },
    data: {
      label: 'John Smith',
      type: 'person',
      description: 'IT Manager responsible for incident resolution',
      properties: { department: 'IT', role: 'Manager', experience: '8 years' },
      source: 'HR Database'
    },
  },
  {
    id: '9',
    type: 'knowledgeNode',
    position: { x: 350, y: 500 },
    data: {
      label: 'Sarah Johnson',
      type: 'person',
      description: 'Sales Manager handling enterprise accounts',
      properties: { department: 'Sales', role: 'Manager', quota: '$1M' },
      source: 'Salesforce'
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'smoothstep',
    style: { stroke: '#6366f1', strokeWidth: 2 },
    label: 'uses',
  },
  {
    id: 'e1-3',
    source: '1',
    target: '3',
    type: 'smoothstep',
    style: { stroke: '#6366f1', strokeWidth: 2 },
    label: 'uses',
  },
  {
    id: 'e2-4',
    source: '2',
    target: '4',
    type: 'smoothstep',
    style: { stroke: '#10b981', strokeWidth: 2 },
    label: 'supports',
  },
  {
    id: 'e2-5',
    source: '2',
    target: '5',
    type: 'smoothstep',
    style: { stroke: '#10b981', strokeWidth: 2 },
    label: 'supports',
  },
  {
    id: 'e3-6',
    source: '3',
    target: '6',
    type: 'smoothstep',
    style: { stroke: '#f59e0b', strokeWidth: 2 },
    label: 'manages',
  },
  {
    id: 'e3-7',
    source: '3',
    target: '7',
    type: 'smoothstep',
    style: { stroke: '#f59e0b', strokeWidth: 2 },
    label: 'tracks',
  },
  {
    id: 'e4-8',
    source: '4',
    target: '8',
    type: 'smoothstep',
    style: { stroke: '#ec4899', strokeWidth: 2 },
    label: 'assigned_to',
  },
  {
    id: 'e7-9',
    source: '7',
    target: '9',
    type: 'smoothstep',
    style: { stroke: '#ec4899', strokeWidth: 2 },
    label: 'owned_by',
  },
];

export const KnowledgeGraph: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNodeType, setSelectedNodeType] = useState('all');
  const [selectedSource, setSelectedSource] = useState('all');

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({
      ...params,
      type: 'smoothstep',
      style: { stroke: '#6366f1', strokeWidth: 2 },
    }, eds)),
    [setEdges]
  );

  // Filter nodes based on search and filters
  const filteredNodes = nodes.filter(node => {
    const matchesSearch = node.data.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         node.data.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedNodeType === 'all' || node.data.type === selectedNodeType;
    const matchesSource = selectedSource === 'all' || node.data.source === selectedSource;
    
    return matchesSearch && matchesType && matchesSource;
  });

  const nodeStats = {
    total: nodes.length,
    entities: nodes.filter(n => n.data.type === 'entity').length,
    processes: nodes.filter(n => n.data.type === 'process').length,
    systems: nodes.filter(n => n.data.type === 'system').length,
    people: nodes.filter(n => n.data.type === 'person').length,
    departments: nodes.filter(n => n.data.type === 'department').length,
    documents: nodes.filter(n => n.data.type === 'document').length,
  };

  const sources = Array.from(new Set(nodes.map(n => n.data.source).filter(Boolean)));

  return (
    <div className="h-full w-full relative">
      {/* Search and Filter Bar */}
      <div className="absolute top-4 left-4 right-4 z-10">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search nodes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
              />
            </div>
            
            <select
              value={selectedNodeType}
              onChange={(e) => setSelectedNodeType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              <option value="all">All Types</option>
              <option value="entity">Entities</option>
              <option value="process">Processes</option>
              <option value="system">Systems</option>
              <option value="person">People</option>
              <option value="department">Departments</option>
              <option value="document">Documents</option>
            </select>
            
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              <option value="all">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
              <Filter className="w-4 h-4" />
            </button>
            
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
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
        
        {/* Graph Statistics Panel */}
        <Panel position="top-right">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-[250px] mt-20">
            <h3 className="font-semibold text-sm text-gray-900 mb-3 flex items-center">
              <Layers className="w-4 h-4 mr-2" />
              Knowledge Graph Stats
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Nodes:</span>
                <span className="font-medium">{nodeStats.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Entities:</span>
                <span className="font-medium text-blue-600">{nodeStats.entities}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Processes:</span>
                <span className="font-medium text-green-600">{nodeStats.processes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Systems:</span>
                <span className="font-medium text-purple-600">{nodeStats.systems}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">People:</span>
                <span className="font-medium text-pink-600">{nodeStats.people}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Departments:</span>
                <span className="font-medium text-indigo-600">{nodeStats.departments}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Relationships:</span>
                <span className="font-medium">{edges.length}</span>
              </div>
            </div>
          </div>
        </Panel>

        {/* Legend Panel */}
        <Panel position="bottom-left">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
            <h3 className="font-semibold text-sm text-gray-900 mb-3">Node Types</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-200 border border-blue-300 rounded"></div>
                <span>Entity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-200 border border-green-300 rounded"></div>
                <span>Process</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-purple-200 border border-purple-300 rounded"></div>
                <span>System</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-pink-200 border border-pink-300 rounded"></div>
                <span>Person</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-indigo-200 border border-indigo-300 rounded"></div>
                <span>Department</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-200 border border-yellow-300 rounded"></div>
                <span>Document</span>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};