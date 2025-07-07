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
        
        <!-- Relationships -->
        <g class="relationships">
          ${relationships.map((rel, i) => {
            const sourceNode = nodes.find(n => n.id === rel.startNodeId || n.id === rel.source);
            const targetNode = nodes.find(n => n.id === rel.endNodeId || n.id === rel.target);
            if (!sourceNode || !targetNode) return '';
            
            const sourceIndex = nodes.indexOf(sourceNode);
            const targetIndex = nodes.indexOf(targetNode);
            
            // Calculate positions in a force-directed layout style
            const sourceX = 150 + (sourceIndex % 5) * 150 + Math.cos(sourceIndex) * 50;
            const sourceY = 150 + Math.floor(sourceIndex / 5) * 150 + Math.sin(sourceIndex) * 50;
            const targetX = 150 + (targetIndex % 5) * 150 + Math.cos(targetIndex) * 50;
            const targetY = 150 + Math.floor(targetIndex / 5) * 150 + Math.sin(targetIndex) * 50;
            
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
          ${nodes.map((node, i) => {
            const x = 150 + (i % 5) * 150 + Math.cos(i) * 50;
            const y = 150 + Math.floor(i / 5) * 150 + Math.sin(i) * 50;
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
                 style="cursor: pointer;"
                 onmouseover="this.querySelector('circle').style.transform='scale(1.1)'; this.querySelector('circle').style.filter='url(#dropshadow)';"
                 onmouseout="this.querySelector('circle').style.transform='scale(1)'; this.querySelector('circle').style.filter='none';"
                 onclick="console.log('Node clicked:', '${node.id}')">
                
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
        
        <!-- Legend -->
        <g class="legend" transform="translate(20, 20)">
          <rect width="200" height="${Object.keys({ Person: '', System: '', Department: '', Process: '', Entity: '', Document: '' }).length * 25 + 20}" 
                fill="white" stroke="#e5e7eb" rx="8" fill-opacity="0.95"/>
          <text x="10" y="15" fill="#374151" font-size="12" font-weight="600">Node Types</text>
          ${Object.entries({
            'Person': '#ec4899',
            'System': '#8b5cf6', 
            'Department': '#3b82f6',
            'Process': '#10b981',
            'Entity': '#f59e0b',
            'Document': '#ef4444'
          }).map(([label, color], idx) => `
            <g transform="translate(10, ${35 + idx * 20})">
              <circle r="6" fill="${color}"/>
              <text x="15" y="4" fill="#374141" font-size="11">${label}</text>
            </g>
          `).join('')}
        </g>
      </svg>
    `;

    container.innerHTML = svg;

    // Add click event listeners
    const nodeElements = container.querySelectorAll('.node');
    nodeElements.forEach(nodeEl => {
      nodeEl.addEventListener('click', (e) => {
        const nodeId = nodeEl.getAttribute('data-id');
        const node = nodes.find(n => n.id === nodeId);
        if (node && onNodeClick) {
          onNodeClick(node);
        }
      });
    });

    const relElements = container.querySelectorAll('.relationship');
    relElements.forEach(relEl => {
      relEl.addEventListener('click', (e) => {
        const relId = relEl.getAttribute('data-id');
        const relationship = relationships.find(r => r.id === relId);
        if (relationship && onRelationshipClick) {
          onRelationshipClick(relationship);
        }
      });
    });

  }, [nodes, relationships, onNodeClick, onRelationshipClick]);

  // Set container ID for NVL
  useEffect(() => {
    if (containerRef.current && !containerRef.current.id) {
      containerRef.current.id = `nvl-container-${Math.random().toString(36).substr(2, 9)}`;
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
      
      {!isLoading && (
        <div className="absolute bottom-4 right-4 bg-white bg-opacity-90 rounded-lg p-2 text-xs text-gray-600">
          {nodes.length} nodes, {relationships.length} relationships
        </div>
      )}
    </div>
  );
};