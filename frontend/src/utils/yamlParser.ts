import { Node, Edge } from '@xyflow/react';

export interface WorkflowNode {
  id: string;
  name: string;
  type?: string;
  description?: string;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  description?: string;
}

export interface ParsedWorkflow {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
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

export function parseYAMLWorkflow(yamlContent: string): ParsedWorkflow | null {
  try {
    // Simple YAML parsing for the specific format we expect
    const lines = yamlContent.split('\n');
    const nodes: WorkflowNode[] = [];
    const edges: WorkflowEdge[] = [];
    
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
        // Save previous item if exists
        if (currentItem.id) {
          if (currentSection === 'nodes') {
            nodes.push(currentItem);
          } else if (currentSection === 'edges') {
            edges.push(currentItem);
          }
        }
        // Start new item
        currentItem = { id: line.replace('- id:', '').trim() };
      } else if (line.includes(':')) {
        const [key, ...valueParts] = line.split(':');
        const value = valueParts.join(':').trim();
        if (key && value) {
          currentItem[key.trim()] = value;
        }
      }
    }
    
    // Add the last item
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

export function convertToReactFlowData(workflow: ParsedWorkflow): ReactFlowData {
  const nodes: Node[] = workflow.nodes.map((node, index) => ({
    id: node.id.toString(),
    type: node.type === 'start' ? 'input' : 'workflowStep',
    position: { 
      x: (index % 3) * 250, 
      // y: Math.floor(index / 3) * 250 
      y: 20+150*index // Adjusted for better vertical spacing
    },
    data: {
      label: node.name,
      description: node.description || '',
      type: node.type || 'default'
    }
  }));
  console.log('Workflow :', workflow);
  const edges: Edge[] = workflow.edges.filter((edge) => ( (edge.source) && (edge.target) )).map((edge) => ({
    id: edge.id.toString(),
    source: edge.source.toString(),
    target: edge.target.toString(),
    // type: edge.type || 'default',
    type: 'smoothstep',
    style: { stroke: '#6366f1', strokeWidth: 2 },
    label: edge.description || ''
  }));
  console.log('Converted edges:', edges);
  return { nodes, edges };
}

export function convertToAgentFlowData(workflow: ParsedWorkflow): ReactFlowData {
  const nodes: Node[] = workflow.nodes.map((node, index) => {
    // Parse agent-specific properties from the node data
    const skills = node.description?.match(/Skills: (.+)/)?.[1]?.split(',').map(s => s.trim()) || [];
    const tools = node.description?.match(/Tools: (.+)/)?.[1]?.split(',').map(s => s.trim()) || [];
    const role = node.type as 'supervisor' | 'specialist' | 'coordinator' | 'executor' || 'executor';
    const department = node.description?.match(/Department: (.+)/)?.[1]?.trim() || 'General';
    
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
        tools: tools,
        description: node.description || 'Agent description',
        status: 'active' as const,
        level: role === 'coordinator' ? 0 : role === 'supervisor' ? 1 : 2,
        department: department,
        maxConcurrentTasks: role === 'coordinator' ? 50 : role === 'supervisor' ? 10 : 5
      }
    };
  });
  
  const edges: Edge[] = workflow.edges.filter((edge) => edge.source && edge.target).map((edge) => ({
    id: edge.id.toString(),
    source: edge.source.toString(),
    target: edge.target.toString(),
    type: 'smoothstep',
    style: { stroke: '#8b5cf6', strokeWidth: 2 },
    label: edge.description || 'delegates to'
  }));
  
  return { nodes, edges };
}

export function isValidYAML(content: string): boolean {
  return content.includes('Nodes:') && content.includes('Edges:');
}