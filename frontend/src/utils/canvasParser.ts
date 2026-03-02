import { Node, Edge } from '@xyflow/react';

export interface CanvasNode {
  id: string;
  name: string;
  type?: string;
  description?: string;
  role?: string;
  skills?: string | string[];
  department?: string;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  description?: string;
}

export interface ParsedCanvas {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}

export interface ReactFlowData {
  nodes: Node[];
  edges: Edge[];
  metadata?: {
    name?: string;
    description?: string;
    category?: string;
    [key: string]: any;
  };
}

export function parseJSONCanvas(jsonContent: string): ParsedCanvas | null {
  try {
    const parsed = JSON.parse(jsonContent);

    // Validate required structure
    if (!parsed.nodes || !Array.isArray(parsed.nodes)) {
      console.error('Invalid JSON: missing nodes array');
      return null;
    }

    if (!parsed.edges || !Array.isArray(parsed.edges)) {
      console.error('Invalid JSON: missing edges array');
      return null;
    }

    return {
      nodes: parsed.nodes,
      edges: parsed.edges
    };
  } catch (error) {
    console.error('Error parsing JSON:', error);
    return null;
  }
}

export function convertToReactFlowData(canvas: ParsedCanvas): ReactFlowData {
  const nodes: Node[] = canvas.nodes.map((node, index) => ({
    id: node.id.toString(),
    type: node.type === 'start' ? 'input' : 'workflowStep',
    position: {
      x: (index % 3) * 250,
      y: 20 + 150 * index
    },
    data: {
      label: node.name,
      description: node.description || '',
      type: node.type || 'default'
    }
  }));

  console.log('Canvas:', canvas);

  const edges: Edge[] = canvas.edges
    .filter((edge) => edge.source && edge.target)
    .map((edge) => ({
      id: edge.id.toString(),
      source: edge.source.toString(),
      target: edge.target.toString(),
      type: 'smoothstep',
      style: { stroke: '#6366f1', strokeWidth: 2 },
      label: edge.description || ''
    }));

  console.log('Converted edges:', edges);

  return { nodes, edges };
}

export function convertToAgentFlowData(canvas: ParsedCanvas): ReactFlowData {
  const nodes: Node[] = canvas.nodes.map((node, index) => {
    // Handle skills as either string or array
    const skills = Array.isArray(node.skills)
      ? node.skills
      : (node.skills?.split(',').map(s => s.trim()) || []);

    const role = (node.role || node.type) as 'supervisor' | 'specialist' | 'coordinator' | 'executor' || 'executor';
    const department = node.department || 'General';

    return {
      id: node.id.toString(),
      type: 'agentNode',
      position: {
        x: (index % 4) * 300 + 50,
        y: Math.floor(index / 4) * 200 + 50
      },
      data: {
        name: node.name,
        role: role,
        skills: skills,
        tools: [],
        description: node.description || 'Agent description',
        status: 'active' as const,
        level: role === 'coordinator' ? 0 : role === 'supervisor' ? 1 : 2,
        department: department,
        maxConcurrentTasks: role === 'coordinator' ? 50 : role === 'supervisor' ? 10 : 5
      }
    };
  });

  const edges: Edge[] = canvas.edges
    .filter((edge) => edge.source && edge.target)
    .map((edge) => ({
      id: edge.id.toString(),
      source: edge.source.toString(),
      target: edge.target.toString(),
      type: 'smoothstep',
      style: { stroke: '#8b5cf6', strokeWidth: 2 },
      label: edge.description || 'delegates to'
    }));

  return { nodes, edges };
}

export function isValidJSON(content: string): boolean {
  try {
    const parsed = JSON.parse(content);
    return parsed.nodes && Array.isArray(parsed.nodes) &&
           parsed.edges && Array.isArray(parsed.edges);
  } catch {
    return false;
  }
}

// Legacy YAML support for backwards compatibility
export function parseYAMLWorkflow(yamlContent: string): ParsedCanvas | null {
  try {
    const lines = yamlContent.split('\n');
    const nodes: CanvasNode[] = [];
    const edges: CanvasEdge[] = [];

    let currentSection = '';
    let currentItem: any = {};

    for (let line of lines) {
      line = line.trim();

      if (line.startsWith('Nodes:')) {
        currentSection = 'nodes';
        continue;
      } else if (line.startsWith('Edges:')) {
        currentSection = 'edges';
        continue;
      }

      if (line.startsWith('- id:')) {
        if (currentItem.id) {
          if (currentSection === 'nodes') {
            nodes.push(currentItem);
          } else if (currentSection === 'edges') {
            edges.push(currentItem);
          }
        }
        currentItem = { id: line.replace('- id:', '').trim() };
      } else if (line.includes(':')) {
        const [key, ...valueParts] = line.split(':');
        const value = valueParts.join(':').trim();
        if (key && value) {
          currentItem[key.trim()] = value;
        }
      }
    }

    if (currentItem.id) {
      if (currentSection === 'nodes') {
        nodes.push(currentItem);
      } else if (currentSection === 'edges') {
        edges.push(currentItem);
      }
    }

    return { nodes, edges };
  } catch (error) {
    console.error('Error parsing YAML:', error);
    return null;
  }
}

export function isValidYAML(content: string): boolean {
  return content.includes('Nodes:') && content.includes('Edges:');
}

// Re-export types with legacy names for compatibility
export type WorkflowNode = CanvasNode;
export type WorkflowEdge = CanvasEdge;
export type ParsedWorkflow = ParsedCanvas;
