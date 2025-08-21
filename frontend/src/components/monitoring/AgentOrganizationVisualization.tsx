import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  addEdge,
  ConnectionLineType,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Bot, 
  Activity, 
  Pause, 
  AlertCircle,
  Zap,
  CheckCircle,
  Clock
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'busy' | 'offline' | 'error';
  type?: string;
  role?: string;
}

interface AgentConnection {
  id: string;
  from_agent_id: string;
  to_agent_id: string;
  type?: 'data_flow' | 'control_flow' | 'feedback';
  status?: 'active' | 'inactive';
}

interface AgentOrganizationVisualizationProps {
  organization: {
    id: string;
    name: string;
    status: string;
    agents_data: Agent[];
    connections_data: AgentConnection[];
  };
}

// Custom node component for agents
const AgentNode: React.FC<{
  data: {
    label: string;
    status: 'active' | 'idle' | 'busy' | 'offline' | 'error';
    type?: string;
    role?: string;
  };
}> = ({ data }) => {
  const getStatusIcon = () => {
    switch (data.status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'busy':
        return <Activity className="w-4 h-4 text-orange-600 animate-pulse" />;
      case 'idle':
        return <Clock className="w-4 h-4 text-gray-600" />;
      case 'offline':
        return <Pause className="w-4 h-4 text-red-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Bot className="w-4 h-4 text-gray-400" />;
    }
  };

  const getNodeClasses = () => {
    const baseClasses = "px-4 py-3 shadow-lg rounded-xl border-2 min-w-[140px] text-center relative";
    switch (data.status) {
      case 'active':
        return `${baseClasses} bg-green-50 border-green-300 text-green-900`;
      case 'busy':
        return `${baseClasses} bg-orange-50 border-orange-300 text-orange-900 animate-pulse`;
      case 'idle':
        return `${baseClasses} bg-gray-50 border-gray-300 text-gray-700`;
      case 'offline':
        return `${baseClasses} bg-red-50 border-red-300 text-red-900`;
      case 'error':
        return `${baseClasses} bg-red-100 border-red-400 text-red-900`;
      default:
        return `${baseClasses} bg-gray-50 border-gray-200 text-gray-600`;
    }
  };

  const getStatusBadge = () => {
    const badgeClasses = "absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white";
    switch (data.status) {
      case 'active':
        return <div className={`${badgeClasses} bg-green-500`} />;
      case 'busy':
        return <div className={`${badgeClasses} bg-orange-500 animate-pulse`} />;
      case 'idle':
        return <div className={`${badgeClasses} bg-gray-500`} />;
      case 'offline':
        return <div className={`${badgeClasses} bg-red-500`} />;
      case 'error':
        return <div className={`${badgeClasses} bg-red-600`} />;
      default:
        return <div className={`${badgeClasses} bg-gray-400`} />;
    }
  };

  return (
    <div className={getNodeClasses()}>
      {getStatusBadge()}
      <div className="flex items-center justify-center space-x-2 mb-1">
        <Bot className="w-5 h-5" />
        <span className="font-semibold text-sm">{data.label}</span>
      </div>
      <div className="flex items-center justify-center space-x-1 mb-1">
        {getStatusIcon()}
        <span className="text-xs capitalize">{data.status}</span>
      </div>
      {(data.role || data.type) && (
        <div className="text-xs text-gray-500 font-medium">
          {data.role || data.type}
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  agentNode: AgentNode,
};

export const AgentOrganizationVisualization: React.FC<AgentOrganizationVisualizationProps> = ({ 
  organization 
}) => {
  // Create nodes and edges from organization data
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const agents = organization.agents_data || [];
    const connections = organization.connections_data || [];

    // Create nodes
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    if (agents.length === 0) {
      // Create demo agents for visualization
      const demoAgents = [
        { id: '1', name: 'Coordinator Agent', status: 'active', role: 'coordinator', type: 'supervisor' },
        { id: '2', name: 'Data Processor', status: 'busy', role: 'processor', type: 'specialist' },
        { id: '3', name: 'Quality Checker', status: 'idle', role: 'validator', type: 'specialist' },
        { id: '4', name: 'Output Handler', status: 'active', role: 'executor', type: 'specialist' },
      ];

      demoAgents.forEach((agent, index) => {
        nodes.push({
          id: agent.id,
          type: 'agentNode',
          position: { 
            x: (index % 2) * 300, 
            y: Math.floor(index / 2) * 150 + (index % 2) * 50
          },
          data: {
            label: agent.name,
            status: agent.status as any,
            role: agent.role,
            type: agent.type,
          },
        });
      });

      // Create demo connections
      const demoConnections = [
        { from: '1', to: '2', type: 'control_flow' },
        { from: '2', to: '3', type: 'data_flow' },
        { from: '3', to: '4', type: 'data_flow' },
        { from: '4', to: '1', type: 'feedback' },
      ];

      demoConnections.forEach((conn, index) => {
        edges.push({
          id: `e${conn.from}-${conn.to}`,
          source: conn.from,
          target: conn.to,
          type: 'smoothstep',
          animated: conn.type === 'data_flow',
          style: {
            stroke: conn.type === 'control_flow' ? '#3B82F6' : 
                   conn.type === 'feedback' ? '#10B981' : '#F59E0B',
            strokeWidth: 2,
          },
          markerEnd: {
            type: 'arrow',
            color: conn.type === 'control_flow' ? '#3B82F6' : 
                   conn.type === 'feedback' ? '#10B981' : '#F59E0B',
          },
        });
      });
    } else {
      // Create nodes from actual agent data
      agents.forEach((agent, index) => {
        const angle = (index * 2 * Math.PI) / agents.length;
        const radius = Math.max(150, agents.length * 30);
        const x = Math.cos(angle) * radius + 300;
        const y = Math.sin(angle) * radius + 200;

        nodes.push({
          id: agent.id || `agent-${index}`,
          type: 'agentNode',
          position: { x, y },
          data: {
            label: agent.name || `Agent ${index + 1}`,
            status: agent.status || 'idle',
            role: agent.role,
            type: agent.type,
          },
        });
      });

      // Create edges from connections data
      connections.forEach((connection, index) => {
        const sourceExists = agents.some(a => a.id === connection.from_agent_id);
        const targetExists = agents.some(a => a.id === connection.to_agent_id);

        if (sourceExists && targetExists) {
          edges.push({
            id: connection.id || `e${connection.from_agent_id}-${connection.to_agent_id}`,
            source: connection.from_agent_id,
            target: connection.to_agent_id,
            type: 'smoothstep',
            animated: connection.status === 'active',
            style: {
              stroke: connection.type === 'control_flow' ? '#3B82F6' : 
                     connection.type === 'feedback' ? '#10B981' : '#F59E0B',
              strokeWidth: 2,
            },
            markerEnd: {
              type: 'arrow',
              color: connection.type === 'control_flow' ? '#3B82F6' : 
                     connection.type === 'feedback' ? '#10B981' : '#F59E0B',
            },
          });
        }
      });
    }

    return { nodes, edges };
  }, [organization]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const getOrganizationStatusColor = () => {
    switch (organization.status) {
      case 'running':
        return '#3B82F6'; // blue
      case 'active':
        return '#10B981'; // green
      case 'paused':
        return '#F59E0B'; // yellow
      case 'inactive':
        return '#6B7280'; // gray
      default:
        return '#6B7280'; // gray
    }
  };

  const getAgentStatusCounts = () => {
    const agents = organization.agents_data || [];
    const counts = {
      active: 0,
      busy: 0,
      idle: 0,
      offline: 0,
      error: 0,
    };

    agents.forEach(agent => {
      const status = agent.status || 'idle';
      if (counts.hasOwnProperty(status)) {
        counts[status as keyof typeof counts]++;
      }
    });

    return counts;
  };

  const statusCounts = getAgentStatusCounts();

  return (
    <div className="h-96 w-full border rounded-lg overflow-hidden">
      <div className="bg-white border-b px-4 py-2">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">
            {organization.name} - Agent Network
          </h4>
          <div className="flex items-center space-x-3 text-sm text-gray-600">
            {statusCounts.active > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>{statusCounts.active} active</span>
              </div>
            )}
            {statusCounts.busy > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                <span>{statusCounts.busy} busy</span>
              </div>
            )}
            {statusCounts.idle > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                <span>{statusCounts.idle} idle</span>
              </div>
            )}
            {statusCounts.offline > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span>{statusCounts.offline} offline</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={20} 
          size={1} 
          color="#e5e7eb" 
        />
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={getOrganizationStatusColor()}
          nodeStrokeWidth={3}
          zoomable
          pannable
          position="top-right"
          style={{
            height: 80,
            width: 120,
          }}
        />
      </ReactFlow>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm p-2 rounded-lg text-xs">
        <div className="font-medium mb-1">Connection Types:</div>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-blue-500"></div>
            <span>Control Flow</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-yellow-500"></div>
            <span>Data Flow</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-green-500"></div>
            <span>Feedback</span>
          </div>
        </div>
      </div>
    </div>
  );
};