import React, { useState, useCallback, useRef, useMemo } from 'react';
import { ReactFlow,
  addEdge,
  Controls,
  Panel,
  type Node,
  type Edge,
  OnConnect,
  Connection,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './ZapierStyles.css';
import { Plus } from 'lucide-react';
import ZapierStepNode, { ZapierStepData } from './ZapierStepNode';
import StepConnector from './StepConnector';
import Menu from "./Menu";
import * as YAML from 'yaml';

interface CanvasComponentProps {
  nodes: Node[];
  edges: Edge[];
  setNodes: any;
  setEdges: any;
  onNodesChange: any;
  onEdgesChange: any;
}

// Custom node types for Zapier-style design
const nodeTypes = {
  zapierStep: ZapierStepNode,
};

// Custom edge style for Zapier
const edgeStyle = {
  stroke: '#e5e7eb',
  strokeWidth: 2,
};

export const CanvasComponent: React.FC<CanvasComponentProps> = ({ 
  nodes, 
  edges, 
  setNodes, 
  setEdges, 
  onNodesChange, 
  onEdgesChange 
}) => {
  const { fitView } = useReactFlow();
  const [fileName, setFileName] = useState('untitled.txt');
  const [showConnectors, setShowConnectors] = useState(true);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Auto-layout nodes vertically in Zapier style
  const layoutNodesVertically = useCallback(() => {
    const VERTICAL_SPACING = 150;
    const CENTER_X = 200;
    
    const layoutedNodes = nodes.map((node, index) => ({
      ...node,
      position: {
        x: CENTER_X,
        y: index * VERTICAL_SPACING + 50
      },
      data: {
        ...node.data,
        stepNumber: index + 1
      }
    }));
    
    setNodes(layoutedNodes);
  }, [nodes, setNodes]);

  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        style: edgeStyle,
        type: 'smoothstep',
        animated: false,
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges],
  );

  // Save workflow to YAML file
  const handleSave = () => {
    console.log(fileName);
    if (!fileName.trim()) {
      alert('Please enter a valid filename');
      return;
    }

    const workflowData = {
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data,
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      })),
    };

    const yamlString = YAML.stringify(workflowData);
    const blob = new Blob([yamlString], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'concerto-flow-' + fileName + '.yaml';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Load workflow from YAML file
  const handleLoad = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const workflowData = YAML.parse(e.target.result);
        setNodes(workflowData.nodes || []);
        setEdges(workflowData.edges || []);
      } catch (error) {
        alert('Error parsing YAML file');
      }
    };
    reader.readAsText(file);
  };

  const addNode = useCallback((insertAfterIndex?: number) => {
    const newNodeId = `step_${Date.now()}`;
    const insertIndex = insertAfterIndex !== undefined ? insertAfterIndex + 1 : nodes.length;
    
    const newNode: Node<ZapierStepData> = {
      id: newNodeId,
      type: 'zapierStep',
      position: { x: 200, y: insertIndex * 150 + 50 },
      data: {
        label: 'New Step',
        app: 'Default',
        action: 'Select an action',
        description: '',
        stepNumber: insertIndex + 1,
        isExpanded: false,
        status: 'idle'
      },
    };

    // Insert the new node at the specified position
    const newNodes = [...nodes];
    newNodes.splice(insertIndex, 0, newNode);
    
    // Update step numbers and positions
    const updatedNodes = newNodes.map((node, index) => ({
      ...node,
      position: { x: 200, y: index * 150 + 50 },
      data: {
        ...node.data,
        stepNumber: index + 1
      }
    }));

    setNodes(updatedNodes);

    // Create edge to connect to previous node
    if (insertIndex > 0) {
      const sourceNodeId = updatedNodes[insertIndex - 1].id;
      const newEdge = {
        id: `edge_${sourceNodeId}_${newNodeId}`,
        source: sourceNodeId,
        target: newNodeId,
        style: edgeStyle,
        type: 'smoothstep',
      };
      setEdges((eds) => [...eds, newEdge]);
    }

    // Update edges that were connected to the node after insertion point
    if (insertIndex < nodes.length) {
      const targetNodeId = nodes[insertIndex].id;
      setEdges((eds) => 
        eds.map(edge => 
          edge.target === targetNodeId 
            ? { ...edge, target: newNodeId }
            : edge
        ).concat({
          id: `edge_${newNodeId}_${targetNodeId}`,
          source: newNodeId,
          target: targetNodeId,
          style: edgeStyle,
          type: 'smoothstep',
        })
      );
    }
  }, [nodes, setNodes, setEdges]);

  const updateNode = useCallback((nodeId: string, newData: Partial<ZapierStepData>) => {
    setNodes((nds) => nds.map((node) => {
      if (node.id === nodeId) {
        return { ...node, data: { ...node.data, ...newData } };
      }
      return node;
    }));
  }, [setNodes]);

  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => {
      const filteredNodes = nds.filter(node => node.id !== nodeId);
      // Re-number and reposition remaining nodes
      return filteredNodes.map((node, index) => ({
        ...node,
        position: { x: 200, y: index * 150 + 50 },
        data: {
          ...node.data,
          stepNumber: index + 1
        }
      }));
    });
    
    // Remove edges connected to this node
    setEdges((eds) => eds.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    ));
  }, [setNodes, setEdges]);

  // Initialize with first step if no nodes exist
  React.useEffect(() => {
    if (nodes.length === 0) {
      addNode();
    }
  }, []);

  // Memoize styled edges
  const styledEdges = useMemo(() => 
    edges.map(edge => ({
      ...edge,
      style: edgeStyle,
      type: 'smoothstep',
    }))
  , [edges]);

  return (
    <div style={{ 
      width: '70vw', 
      height: '90vh',
      background: '#f8fafc',
      position: 'relative'
    }}>
      {/* Zapier-style Header */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: '#fff',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        zIndex: 100
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px'
        }}>
          <h2 style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: '600',
            color: '#1f2937'
          }}>
            Workflow Designer
          </h2>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            color: '#6b7280'
          }}>
            <span>{nodes.length} steps</span>
            <span>•</span>
            <span>Draft</span>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <button
            onClick={layoutNodesVertically}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              background: '#fff',
              color: '#374151',
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            Auto Layout
          </button>
          <button
            onClick={() => addNode()}
            style={{
              padding: '8px 16px',
              background: '#ff4f00',
              border: 'none',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Plus size={14} />
            Add Step
          </button>
        </div>
      </div>

      {/* ReactFlow Canvas */}
      <div style={{ 
        marginTop: '60px',
        height: 'calc(100% - 60px)',
        background: '#f8fafc'
      }}>
        <ReactFlow
          nodes={nodes}
          edges={styledEdges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          fitViewOptions={{
            padding: 40,
            includeHiddenNodes: false,
          }}
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          minZoom={0.5}
          maxZoom={2}
          snapToGrid={false}
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          selectNodesOnDrag={false}
          panOnDrag={true}
          panOnScroll={true}
          zoomOnScroll={true}
          zoomOnPinch={true}
          deleteKeyCode="Delete"
          style={{
            background: '#f8fafc',
          }}
        >
          {/* Simplified Controls */}
          <Controls 
            position="bottom-right"
            style={{
              button: {
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
              }
            }}
          />
          
          {/* Add Step at End Button */}
          {nodes.length > 0 && (
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: nodes.length * 150 + 100,
                transform: 'translateX(-50%)',
                zIndex: 10
              }}
            >
              <button
                onClick={() => addNode()}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: '#fff',
                  border: '2px dashed #d1d5db',
                  color: '#9ca3af',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#ff4f00';
                  e.currentTarget.style.color = '#ff4f00';
                  e.currentTarget.style.background = '#fff7ed';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#d1d5db';
                  e.currentTarget.style.color = '#9ca3af';
                  e.currentTarget.style.background = '#fff';
                }}
                title="Add step"
              >
                <Plus size={18} />
              </button>
            </div>
          )}
        </ReactFlow>
      </div>

      {/* Keep the Menu for file operations but hidden/minimal */}
      <div style={{ display: 'none' }}>
        <Menu 
          onSave={handleSave} 
          fileName={fileName} 
          setFileName={setFileName} 
          onLoadFlow={handleLoad} 
          onAddNode={addNode} 
        />
      </div>
    </div>
  );
};

// export default CanvasComponent;
