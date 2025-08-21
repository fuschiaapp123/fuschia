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
  CheckCircle, 
  Play, 
  Clock, 
  XCircle, 
  Pause,
  AlertCircle
} from 'lucide-react';

interface WorkflowTask {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  type?: string;
  dependencies?: string[];
}

interface WorkflowExecutionVisualizationProps {
  execution: {
    id: string;
    workflow_name: string;
    status: string;
    current_tasks: WorkflowTask[];
    completed_tasks: WorkflowTask[];
    failed_tasks: WorkflowTask[];
  };
}

// Custom node component for workflow tasks
const TaskNode: React.FC<{
  data: {
    label: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
    type?: string;
  };
}> = ({ data }) => {
  const getStatusIcon = () => {
    switch (data.status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'in_progress':
        return <Play className="w-4 h-4 text-blue-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getNodeClasses = () => {
    const baseClasses = "px-4 py-2 shadow-md rounded-lg border-2 min-w-[120px] text-center";
    switch (data.status) {
      case 'completed':
        return `${baseClasses} bg-green-100 border-green-300 text-green-900`;
      case 'in_progress':
        return `${baseClasses} bg-blue-100 border-blue-300 text-blue-900 animate-pulse`;
      case 'failed':
        return `${baseClasses} bg-red-100 border-red-300 text-red-900`;
      case 'paused':
        return `${baseClasses} bg-yellow-100 border-yellow-300 text-yellow-900`;
      case 'pending':
        return `${baseClasses} bg-gray-100 border-gray-300 text-gray-700`;
      default:
        return `${baseClasses} bg-gray-50 border-gray-200 text-gray-600`;
    }
  };

  return (
    <div className={getNodeClasses()}>
      <div className="flex items-center justify-center space-x-2">
        {getStatusIcon()}
        <span className="font-medium text-sm">{data.label}</span>
      </div>
      {data.type && (
        <div className="text-xs text-gray-500 mt-1">{data.type}</div>
      )}
    </div>
  );
};

const nodeTypes = {
  taskNode: TaskNode,
};

export const WorkflowExecutionVisualization: React.FC<WorkflowExecutionVisualizationProps> = ({ 
  execution 
}) => {
  // Create nodes and edges from execution data
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const allTasks = [
      ...execution.completed_tasks.map(task => ({ ...task, status: 'completed' as const })),
      ...execution.current_tasks.map(task => ({ ...task, status: 'in_progress' as const })),
      ...execution.failed_tasks.map(task => ({ ...task, status: 'failed' as const })),
    ];

    // Create nodes
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // If we don't have task data, create a simple visualization based on execution status
    if (allTasks.length === 0) {
      // Create a simple flow for demonstration
      const demoTasks = [
        { id: '1', name: 'Start Process', status: 'completed', type: 'start' },
        { id: '2', name: 'Data Processing', status: execution.status === 'completed' ? 'completed' : 'in_progress', type: 'process' },
        { id: '3', name: 'Validation', status: execution.status === 'completed' ? 'completed' : 'pending', type: 'validation' },
        { id: '4', name: 'Complete', status: execution.status === 'completed' ? 'completed' : 'pending', type: 'end' },
      ];

      demoTasks.forEach((task, index) => {
        nodes.push({
          id: task.id,
          type: 'taskNode',
          position: { x: index * 200, y: 100 },
          data: {
            label: task.name,
            status: task.status as any,
            type: task.type,
          },
        });

        // Create edges between consecutive tasks
        if (index > 0) {
          edges.push({
            id: `e${demoTasks[index - 1].id}-${task.id}`,
            source: demoTasks[index - 1].id,
            target: task.id,
            type: 'smoothstep',
            animated: task.status === 'in_progress',
          });
        }
      });
    } else {
      // Create nodes from actual task data
      allTasks.forEach((task, index) => {
        nodes.push({
          id: task.id || `task-${index}`,
          type: 'taskNode',
          position: { x: (index % 4) * 200, y: Math.floor(index / 4) * 100 },
          data: {
            label: task.name || `Task ${index + 1}`,
            status: task.status,
            type: task.type,
          },
        });

        // Create edges based on dependencies
        if (task.dependencies) {
          task.dependencies.forEach(depId => {
            const sourceTask = allTasks.find(t => t.id === depId);
            if (sourceTask) {
              edges.push({
                id: `e${depId}-${task.id}`,
                source: depId,
                target: task.id || `task-${index}`,
                type: 'smoothstep',
                animated: task.status === 'in_progress',
              });
            }
          });
        } else if (index > 0) {
          // Default linear flow if no dependencies specified
          const prevTaskId = allTasks[index - 1].id || `task-${index - 1}`;
          edges.push({
            id: `e${prevTaskId}-${task.id || `task-${index}`}`,
            source: prevTaskId,
            target: task.id || `task-${index}`,
            type: 'smoothstep',
            animated: task.status === 'in_progress',
          });
        }
      });
    }

    return { nodes, edges };
  }, [execution]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const getExecutionStatusColor = () => {
    switch (execution.status) {
      case 'running':
        return '#3B82F6'; // blue
      case 'completed':
        return '#10B981'; // green
      case 'failed':
        return '#EF4444'; // red
      case 'paused':
        return '#F59E0B'; // yellow
      default:
        return '#6B7280'; // gray
    }
  };

  return (
    <div className="h-96 w-full border rounded-lg overflow-hidden">
      <div className="bg-white border-b px-4 py-2">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">
            {execution.workflow_name} - Execution Flow
          </h4>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>✅ {execution.completed_tasks.length} completed</span>
            <span>⏳ {execution.current_tasks.length} in progress</span>
            {execution.failed_tasks.length > 0 && (
              <span className="text-red-600">❌ {execution.failed_tasks.length} failed</span>
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
          nodeColor={getExecutionStatusColor()}
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
    </div>
  );
};