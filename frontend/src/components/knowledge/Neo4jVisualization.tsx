import React, { useEffect, useRef, useState, useCallback } from 'react';

// This will be the actual NVL implementation once the package is properly installed
// For now, this demonstrates the structure and will work with mock data

declare global {
  interface Window {
    // @ts-ignore
    NVL: any;
  }
}

interface Neo4jVisualizationProps {
  nodes: any[];
  relationships: any[];
  onNodeClick?: (node: any) => void;
  onRelationshipClick?: (relationship: any) => void;
  config?: {
    layout?: string;
    physics?: boolean;
    nodeStyle?: any;
    relationshipStyle?: any;
  };
}

interface NodePosition {
  id: string;
  x: number;
  y: number;
}

export const Neo4jVisualization: React.FC<Neo4jVisualizationProps> = ({
  nodes = [],
  relationships = [],
  onNodeClick,
  onRelationshipClick,
  config = {}
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const nvlInstanceRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodePositions, setNodePositions] = useState<NodePosition[]>([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [dragState, setDragState] = useState<{
    isDragging: boolean;
    hasMoved: boolean;
    nodeId: string | null;
    startX: number;
    startY: number;
    currentX: number;
    currentY: number;
  }>({
    isDragging: false,
    hasMoved: false,
    nodeId: null,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0
  });

  const [panState, setPanState] = useState<{
    isPanning: boolean;
    startX: number;
    startY: number;
    startPanX: number;
    startPanY: number;
  }>({
    isPanning: false,
    startX: 0,
    startY: 0,
    startPanX: 0,
    startPanY: 0
  });

  // Initialize NVL
  useEffect(() => {
    const initializeNVL = async () => {
      try {
        if (!containerRef.current) return;

        // Check if NVL is available
        if (typeof window !== 'undefined' && window.NVL) {
          // Create NVL instance with actual library
          const nvlConfig = {
            containerId: containerRef.current.id,
            neo4jd3: {
              highlight: [
                {
                  class: 'highlighted',
                  property: 'highlighted',
                  value: true
                }
              ],
              icons: {
                'Person': 'user',
                'System': 'cog',
                'Department': 'building',
                'Process': 'zap',
                'Entity': 'database',
                'Document': 'file-text'
              },
              images: {
                'Person': '/icons/person.svg',
                'System': '/icons/system.svg'
              },
              minCollision: 60,
              neo4jDataUrl: undefined,
              nodeRadius: 25,
              onNodeDoubleClick: onNodeClick,
              onRelationshipDoubleClick: onRelationshipClick,
              zoomFit: true,
              ...config
            }
          };

          nvlInstanceRef.current = new window.NVL(nvlConfig);
          nvlInstanceRef.current.updateData({ nodes, relationships });
          
        } else {
          // Fallback: Create custom SVG visualization
          createFallbackVisualization();
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error('Failed to initialize NVL:', err);
        setError('Failed to initialize graph visualization');
        createFallbackVisualization();
        setIsLoading(false);
      }
    };

    initializeNVL();

    return () => {
      if (nvlInstanceRef.current && nvlInstanceRef.current.destroy) {
        nvlInstanceRef.current.destroy();
      }
    };
  }, []);

  // Initialize node positions
  useEffect(() => {
    if (nodes.length > 0) {
      const initialPositions = nodes.map((node, i) => ({
        id: node.id,
        x: 150 + (i % 5) * 150 + Math.cos(i) * 50,
        y: 150 + Math.floor(i / 5) * 150 + Math.sin(i) * 50
      }));
      setNodePositions(initialPositions);
    }
  }, [nodes]);

  // Update data when props change
  useEffect(() => {
    if (nvlInstanceRef.current && !isLoading) {
      try {
        nvlInstanceRef.current.updateData({ nodes, relationships });
      } catch (err) {
        console.error('Failed to update graph data:', err);
        createFallbackVisualization();
      }
    }
  }, [nodes, relationships, isLoading]);

  // Handle drag events
  const handleMouseDown = useCallback((e: MouseEvent, nodeId: string) => {
    e.preventDefault();
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const nodePos = nodePositions.find(p => p.id === nodeId);
    if (!nodePos) return;

    setDragState({
      isDragging: true,
      hasMoved: false,
      nodeId,
      startX: e.clientX - rect.left,
      startY: e.clientY - rect.top,
      currentX: nodePos.x,
      currentY: nodePos.y
    });
  }, [nodePositions]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragState.isDragging || !dragState.nodeId) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;
    const deltaX = currentX - dragState.startX;
    const deltaY = currentY - dragState.startY;

    const newX = dragState.currentX + deltaX;
    const newY = dragState.currentY + deltaY;

    // Mark as moved if significant movement
    if (!dragState.hasMoved && (Math.abs(deltaX) > 5 || Math.abs(deltaY) > 5)) {
      setDragState(prev => ({ ...prev, hasMoved: true }));
    }

    setNodePositions(prev => 
      prev.map(pos => 
        pos.id === dragState.nodeId 
          ? { ...pos, x: newX, y: newY }
          : pos
      )
    );
  }, [dragState]);

  const handleMouseUp = useCallback(() => {
    setDragState({
      isDragging: false,
      hasMoved: false,
      nodeId: null,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0
    });
  }, []);

  // Add global mouse event listeners
  useEffect(() => {
    if (dragState.isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragState.isDragging, handleMouseMove, handleMouseUp]);

  // Zoom functions
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev * 1.2, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.1));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // Handle mouse wheel zoom
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoomLevel(prev => Math.max(0.1, Math.min(3, prev * delta)));
  }, []);

  // Add wheel event listener
  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
      return () => {
        container.removeEventListener('wheel', handleWheel);
      };
    }
  }, [handleWheel]);

  // Pan handlers
  const handlePanStart = useCallback((e: MouseEvent) => {
    // Only start panning if not clicking on a node
    const target = e.target as Element;
    if (target.closest('.node')) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    setPanState({
      isPanning: true,
      startX: e.clientX - rect.left,
      startY: e.clientY - rect.top,
      startPanX: panOffset.x,
      startPanY: panOffset.y
    });
  }, [panOffset]);

  const handlePanMove = useCallback((e: MouseEvent) => {
    if (!panState.isPanning) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;
    const deltaX = currentX - panState.startX;
    const deltaY = currentY - panState.startY;

    setPanOffset({
      x: panState.startPanX + deltaX,
      y: panState.startPanY + deltaY
    });
  }, [panState]);

  const handlePanEnd = useCallback(() => {
    setPanState({
      isPanning: false,
      startX: 0,
      startY: 0,
      startPanX: 0,
      startPanY: 0
    });
  }, []);

  // Add pan event listeners
  useEffect(() => {
    if (panState.isPanning) {
      document.addEventListener('mousemove', handlePanMove);
      document.addEventListener('mouseup', handlePanEnd);
      return () => {
        document.removeEventListener('mousemove', handlePanMove);
        document.removeEventListener('mouseup', handlePanEnd);
      };
    }
  }, [panState.isPanning, handlePanMove, handlePanEnd]);

  const createFallbackVisualization = useCallback(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    // Create SVG with D3-like visualization
    const svg = `
      <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" style="background: #fafafa; border-radius: 8px;">
        <defs>
          <!-- Gradient definitions -->
          <radialGradient id="nodeGradient" cx="30%" cy="30%">
            <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.8" />
            <stop offset="100%" style="stop-color:#6366f1;stop-opacity:1" />
          </radialGradient>
          
          <!-- Arrow marker -->
          <marker id="arrowhead" markerWidth="12" markerHeight="8" 
                  refX="11" refY="4" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L0,8 L12,4 z" fill="#6b7280" />
          </marker>
          
          <!-- Shadow filter -->
          <filter id="dropshadow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#00000020"/>
          </filter>
        </defs>
        
        <!-- Main content group with zoom/pan transform -->
        <g class="main-content" transform="translate(${panOffset.x}, ${panOffset.y}) scale(${zoomLevel})">
        
        <!-- Relationships -->
        <g class="relationships">
          ${relationships.map((rel) => {
            const sourceNode = nodes.find(n => n.id === rel.startNodeId || n.id === rel.source);
            const targetNode = nodes.find(n => n.id === rel.endNodeId || n.id === rel.target);
            if (!sourceNode || !targetNode) return '';
            
            // Use dynamic positions from state
            const sourcePos = nodePositions.find(p => p.id === sourceNode.id);
            const targetPos = nodePositions.find(p => p.id === targetNode.id);
            
            if (!sourcePos || !targetPos) return '';
            
            const sourceX = sourcePos.x;
            const sourceY = sourcePos.y;
            const targetX = targetPos.x;
            const targetY = targetPos.y;
            
            // Calculate arrow position
            const dx = targetX - sourceX;
            const dy = targetY - sourceY;
            const length = Math.sqrt(dx * dx + dy * dy);
            const unitX = dx / length;
            const unitY = dy / length;
            const arrowStartX = sourceX + unitX * 35;
            const arrowStartY = sourceY + unitY * 35;
            const arrowEndX = targetX - unitX * 35;
            const arrowEndY = targetY - unitY * 35;
            
            return `
              <g class="relationship" data-id="${rel.id}">
                <line x1="${arrowStartX}" y1="${arrowStartY}" 
                      x2="${arrowEndX}" y2="${arrowEndY}" 
                      stroke="#6b7280" stroke-width="2" 
                      marker-end="url(#arrowhead)"
                      style="cursor: pointer;"
                      onmouseover="this.style.stroke='#3b82f6'; this.style.strokeWidth='3';"
                      onmouseout="this.style.stroke='#6b7280'; this.style.strokeWidth='2';" />
                <text x="${(arrowStartX + arrowEndX) / 2}" y="${(arrowStartY + arrowEndY) / 2 - 8}" 
                      text-anchor="middle" fill="#374151" font-size="11" font-weight="500"
                      style="pointer-events: none;">
                  ${rel.type || rel.relationship || ''}
                </text>
              </g>
            `;
          }).join('')}
        </g>
        
        <!-- Nodes -->
        <g class="nodes">
          ${nodes.map((node) => {
            // Use dynamic positions from state
            const nodePos = nodePositions.find(p => p.id === node.id);
            if (!nodePos) return '';
            
            const x = nodePos.x;
            const y = nodePos.y;
            const labels = node.labels || [node.label] || ['Node'];
            const primaryLabel = labels[0];
            
            // Color based on node type
            const colors = {
              'Person': '#ec4899',
              'System': '#8b5cf6', 
              'Department': '#3b82f6',
              'Process': '#10b981',
              'Entity': '#f59e0b',
              'Document': '#ef4444'
            };
            const color = colors[primaryLabel as keyof typeof colors] || '#6b7280';
            
            return `
              <g class="node" data-id="${node.id}" transform="translate(${x}, ${y})"
                 style="cursor: ${dragState.isDragging && dragState.nodeId === node.id ? 'grabbing' : 'grab'};"
                 onmouseover="this.querySelector('circle').style.transform='scale(1.1)'; this.querySelector('circle').style.filter='url(#dropshadow)';"
                 onmouseout="this.querySelector('circle').style.transform='scale(1)'; this.querySelector('circle').style.filter='none';">
                
                <!-- Node circle -->
                <circle r="30" fill="${color}" stroke="#ffffff" stroke-width="3" 
                        style="transition: all 0.2s ease;"/>
                
                <!-- Node icon/text -->
                <text y="5" text-anchor="middle" fill="white" font-size="12" font-weight="bold"
                      style="pointer-events: none;">
                  ${primaryLabel.substring(0, 3).toUpperCase()}
                </text>
                
                <!-- Node label -->
                <text y="50" text-anchor="middle" fill="#374151" font-size="12" font-weight="500"
                      style="pointer-events: none;">
                  ${(node.properties?.name || node.name || node.id).substring(0, 15)}
                </text>
                
                <!-- Additional labels -->
                ${labels.slice(1).map((label, idx) => `
                  <text y="${65 + idx * 12}" text-anchor="middle" fill="#6b7280" font-size="10"
                        style="pointer-events: none;">
                    ${label}
                  </text>
                `).join('')}
              </g>
            `;
          }).join('')}
        </g>
        
        </g> <!-- End main-content group -->
        
        
        
      </svg>
    `;

    container.innerHTML = svg;

    // Add pan event listener to the container
    container.addEventListener('mousedown', handlePanStart);

    // Add click and drag event listeners
    const nodeElements = container.querySelectorAll('.node');
    nodeElements.forEach(nodeEl => {
      const nodeId = nodeEl.getAttribute('data-id');
      const node = nodes.find(n => n.id === nodeId);
      
      if (node) {
        // Handle mousedown for drag
        const handleNodeMouseDown = (e: Event) => {
          const mouseEvent = e as MouseEvent;
          if (nodeId) {
            handleMouseDown(mouseEvent, nodeId);
          }
        };
        
        // Handle click for selection
        const handleClick = (e: Event) => {
          e.stopPropagation();
          if (onNodeClick) {
            onNodeClick(node);
          }
        };
        
        nodeEl.addEventListener('mousedown', handleNodeMouseDown);
        nodeEl.addEventListener('click', handleClick);
      }
    });

    const relElements = container.querySelectorAll('.relationship');
    relElements.forEach(relEl => {
      relEl.addEventListener('click', () => {
        const relId = relEl.getAttribute('data-id');
        const relationship = relationships.find(r => r.id === relId);
        if (relationship && onRelationshipClick) {
          onRelationshipClick(relationship);
        }
      });
    });

  }, [nodes, relationships, onNodeClick, onRelationshipClick, nodePositions, dragState, zoomLevel, panOffset, handlePanStart]);

  // Update visualization when positions change
  useEffect(() => {
    if (nodePositions.length > 0 && !isLoading) {
      createFallbackVisualization();
    }
  }, [nodePositions, createFallbackVisualization, isLoading]);

  // Set container ID for NVL
  useEffect(() => {
    if (containerRef.current && !containerRef.current.id) {
      containerRef.current.id = `nvl-container-${Math.random().toString(36).substring(2, 11)}`;
    }
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-red-500 mb-2">⚠️</div>
          <div className="text-gray-600">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-gray-600">Loading graph...</div>
          </div>
        </div>
      )}
      
      <div
        ref={containerRef}
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
      
      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        <button
          onClick={handleZoomIn}
          className="w-8 h-8 bg-white shadow-md rounded border hover:bg-gray-50 flex items-center justify-center text-gray-600"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          className="w-8 h-8 bg-white shadow-md rounded border hover:bg-gray-50 flex items-center justify-center text-gray-600"
          title="Zoom Out"
        >
          −
        </button>
        <button
          onClick={handleZoomReset}
          className="w-8 h-8 bg-white shadow-md rounded border hover:bg-gray-50 flex items-center justify-center text-gray-600 text-xs"
          title="Reset Zoom"
        >
          ⌂
        </button>
      </div>
      
      {/* Zoom Level Indicator */}
      <div className="absolute top-4 left-4 bg-white bg-opacity-90 rounded px-2 py-1 text-xs text-gray-600">
        Zoom: {Math.round(zoomLevel * 100)}%
      </div>
      
      {!isLoading && (
        <div className="absolute bottom-4 right-4 bg-white bg-opacity-90 rounded-lg p-2 text-xs text-gray-600">
          {nodes.length} nodes, {relationships.length} relationships
        </div>
      )}
    </div>
  );
};