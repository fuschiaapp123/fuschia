import React, { useState, useCallback, useRef } from 'react';
import { 
  Plus, 
  Save, 
  Download, 
  Upload, 
  Undo, 
  Redo, 
  ZoomIn, 
  ZoomOut, 
  Move,
  Square,
  Circle,
  ArrowRight,
  Clock,
  Users,
  AlertTriangle,
  Settings,
  TrendingUp
} from 'lucide-react';

interface ValueStreamNode {
  id: string;
  type: 'process' | 'decision' | 'delay' | 'inventory' | 'transport' | 'inspection';
  x: number;
  y: number;
  width: number;
  height: number;
  title: string;
  description: string;
  leadTime?: string;
  processTime?: string;
  resources?: string[];
  issues?: string[];
}

interface ValueStreamConnection {
  id: string;
  fromId: string;
  toId: string;
  type: 'material' | 'information' | 'both';
  label?: string;
}

export const ValueStreamDesigner: React.FC = () => {
  const [nodes, setNodes] = useState<ValueStreamNode[]>([]);
  const [connections, setConnections] = useState<ValueStreamConnection[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [selectedTool, setSelectedTool] = useState<string>('select');
  const [showProperties, setShowProperties] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  const nodeTypes = [
    { id: 'process', label: 'Process', icon: Square, color: 'bg-blue-500' },
    { id: 'decision', label: 'Decision', icon: Circle, color: 'bg-orange-500' },
    { id: 'delay', label: 'Delay', icon: Clock, color: 'bg-red-500' },
    { id: 'inventory', label: 'Inventory', icon: Square, color: 'bg-green-500' },
    { id: 'transport', label: 'Transport', icon: ArrowRight, color: 'bg-purple-500' },
    { id: 'inspection', label: 'Inspection', icon: AlertTriangle, color: 'bg-yellow-500' }
  ];

  const addNode = useCallback((type: string) => {
    const newNode: ValueStreamNode = {
      id: `node-${Date.now()}`,
      type: type as any,
      x: 100 + Math.random() * 200,
      y: 100 + Math.random() * 200,
      width: 120,
      height: 80,
      title: `New ${type}`,
      description: '',
      leadTime: '',
      processTime: '',
      resources: [],
      issues: []
    };
    setNodes(prev => [...prev, newNode]);
  }, []);

  const handleNodeMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (selectedTool === 'select') {
      setSelectedNode(nodeId);
      setIsDragging(true);
      
      const node = nodes.find(n => n.id === nodeId);
      if (node) {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
          const clientX = e.clientX - rect.left;
          const clientY = e.clientY - rect.top;
          setDragOffset({
            x: clientX - (node.x * zoomLevel + panOffset.x),
            y: clientY - (node.y * zoomLevel + panOffset.y)
          });
        }
      }
    }
  }, [selectedTool, nodes, zoomLevel, panOffset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && selectedNode) {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const clientX = e.clientX - rect.left;
        const clientY = e.clientY - rect.top;
        
        const newX = (clientX - dragOffset.x - panOffset.x) / zoomLevel;
        const newY = (clientY - dragOffset.y - panOffset.y) / zoomLevel;
        
        setNodes(prev => prev.map(node => 
          node.id === selectedNode 
            ? { ...node, x: newX, y: newY }
            : node
        ));
      }
    }
  }, [isDragging, selectedNode, dragOffset, zoomLevel, panOffset]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.3));
  };

  const handleSave = () => {
    const valueStream = {
      nodes,
      connections,
      metadata: {
        name: 'Untitled Value Stream',
        version: '1.0',
        createdAt: new Date().toISOString()
      }
    };
    
    const blob = new Blob([JSON.stringify(valueStream, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'value-stream.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const NodeComponent: React.FC<{ node: ValueStreamNode }> = ({ node }) => {
    const nodeType = nodeTypes.find(t => t.id === node.type);
    const Icon = nodeType?.icon || Square;
    
    return (
      <div
        className={`absolute border-2 rounded-lg cursor-pointer transition-all ${
          selectedNode === node.id 
            ? 'border-blue-500 shadow-lg' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        style={{
          left: node.x,
          top: node.y,
          width: node.width,
          height: node.height,
          transform: `scale(${zoomLevel})`,
          transformOrigin: 'top left'
        }}
        onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
        onClick={() => setSelectedNode(node.id)}
      >
        <div className={`w-full h-full ${nodeType?.color || 'bg-gray-500'} text-white rounded-lg p-2 flex flex-col items-center justify-center`}>
          <Icon className="w-6 h-6 mb-1" />
          <span className="text-xs font-medium text-center">{node.title}</span>
          {node.leadTime && (
            <span className="text-xs opacity-75 mt-1">{node.leadTime}</span>
          )}
        </div>
      </div>
    );
  };

  const selectedNodeData = nodes.find(n => n.id === selectedNode);

  return (
    <div className="flex h-full">
      {/* Left Panel - Tools */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
        <div className="space-y-6">
          {/* Canvas Tools */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Canvas Tools</h3>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setSelectedTool('select')}
                className={`p-2 rounded-md border ${
                  selectedTool === 'select' 
                    ? 'bg-blue-500 text-white border-blue-500' 
                    : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                }`}
              >
                <Move className="w-4 h-4 mx-auto" />
                <span className="text-xs mt-1 block">Select</span>
              </button>
              <button
                onClick={() => setSelectedTool('pan')}
                className={`p-2 rounded-md border ${
                  selectedTool === 'pan' 
                    ? 'bg-blue-500 text-white border-blue-500' 
                    : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                }`}
              >
                <Move className="w-4 h-4 mx-auto" />
                <span className="text-xs mt-1 block">Pan</span>
              </button>
            </div>
          </div>

          {/* Node Types */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Add Elements</h3>
            <div className="space-y-2">
              {nodeTypes.map(nodeType => {
                const Icon = nodeType.icon;
                return (
                  <button
                    key={nodeType.id}
                    onClick={() => addNode(nodeType.id)}
                    className="w-full flex items-center space-x-3 p-2 rounded-md hover:bg-gray-50 text-left"
                  >
                    <div className={`w-6 h-6 ${nodeType.color} rounded flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm text-gray-700">{nodeType.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">Actions</h3>
            <div className="space-y-2">
              <button
                onClick={handleSave}
                className="w-full flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button className="w-full flex items-center space-x-2 px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
              <button className="w-full flex items-center space-x-2 px-3 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">
                <Upload className="w-4 h-4" />
                <span>Import</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top Toolbar */}
        <div className="bg-white border-b border-gray-200 p-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button className="p-2 hover:bg-gray-100 rounded-md">
              <Undo className="w-4 h-4" />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-md">
              <Redo className="w-4 h-4" />
            </button>
            <div className="border-l border-gray-300 h-6 mx-2"></div>
            <button onClick={handleZoomOut} className="p-2 hover:bg-gray-100 rounded-md">
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-600">{Math.round(zoomLevel * 100)}%</span>
            <button onClick={handleZoomIn} className="p-2 hover:bg-gray-100 rounded-md">
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowProperties(!showProperties)}
              className={`p-2 rounded-md ${
                showProperties 
                  ? 'bg-blue-500 text-white' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 bg-gray-50 overflow-hidden relative">
          <div
            ref={canvasRef}
            className="w-full h-full relative cursor-crosshair"
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{
              backgroundImage: `
                radial-gradient(circle at 1px 1px, rgba(0,0,0,0.1) 1px, transparent 0),
                radial-gradient(circle at 1px 1px, rgba(0,0,0,0.1) 1px, transparent 0)
              `,
              backgroundSize: `${20 * zoomLevel}px ${20 * zoomLevel}px`,
              backgroundPosition: `${panOffset.x}px ${panOffset.y}px`
            }}
          >
            {/* Render Nodes */}
            {nodes.map(node => (
              <NodeComponent key={node.id} node={node} />
            ))}
            
            {/* Canvas Instructions */}
            {nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Start Building Your Value Stream</h3>
                  <p className="text-sm">
                    Add elements from the left panel to begin designing your value stream map
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - Properties */}
      {showProperties && selectedNodeData && (
        <div className="w-80 bg-white border-l border-gray-200 p-4 overflow-y-auto">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Properties</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={selectedNodeData.title}
                    onChange={(e) => setNodes(prev => prev.map(node => 
                      node.id === selectedNode 
                        ? { ...node, title: e.target.value }
                        : node
                    ))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={selectedNodeData.description}
                    onChange={(e) => setNodes(prev => prev.map(node => 
                      node.id === selectedNode 
                        ? { ...node, description: e.target.value }
                        : node
                    ))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lead Time
                  </label>
                  <input
                    type="text"
                    value={selectedNodeData.leadTime || ''}
                    onChange={(e) => setNodes(prev => prev.map(node => 
                      node.id === selectedNode 
                        ? { ...node, leadTime: e.target.value }
                        : node
                    ))}
                    placeholder="e.g., 2 days"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Process Time
                  </label>
                  <input
                    type="text"
                    value={selectedNodeData.processTime || ''}
                    onChange={(e) => setNodes(prev => prev.map(node => 
                      node.id === selectedNode 
                        ? { ...node, processTime: e.target.value }
                        : node
                    ))}
                    placeholder="e.g., 4 hours"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <button
                    onClick={() => setNodes(prev => prev.filter(node => node.id !== selectedNode))}
                    className="w-full px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                  >
                    Delete Element
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};