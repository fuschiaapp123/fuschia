import React, { useCallback, useState } from 'react';
import {
  ReactFlow,
  Node,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Plus } from 'lucide-react';

// Simple node type
const SimpleNode: React.FC<{ data: { label: string } }> = ({ data }) => {
  return (
    <div className="px-4 py-2 bg-blue-100 border-2 border-blue-300 rounded-lg">
      {data.label}
    </div>
  );
};

const nodeTypes = {
  simpleNode: SimpleNode,
};

const WorkflowDesignerSimple: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const addNewNode = useCallback(() => {
    console.log('🚀 Adding new node, current count:', nodes.length);
    
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'simpleNode',
      position: { 
        x: 100 + (nodes.length % 3) * 200, 
        y: 100 + Math.floor(nodes.length / 3) * 150 
      },
      data: {
        label: `Node ${nodes.length + 1}`,
      },
    };
    
    console.log('✨ Creating node:', newNode);
    setNodes((nds) => [...nds, newNode]);
  }, [nodes, setNodes]);

  return (
    <div className="w-full h-screen">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gray-50"
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls />
        <MiniMap />
        
        {/* Simple positioned button outside Panel */}
        <div className="absolute top-4 left-4 z-50">
          <button
            onClick={addNewNode}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors shadow-lg"
          >
            <Plus className="w-4 h-4" />
            <span>Add Node</span>
          </button>
        </div>
      </ReactFlow>
    </div>
  );
};

export default WorkflowDesignerSimple;