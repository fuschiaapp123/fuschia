import { Node, Edge } from '@xyflow/react';
import { parseYAMLWorkflow, convertToReactFlowData, convertToAgentFlowData, isValidYAML } from '@/utils/yamlParser';
import { useAppStore } from '@/store/appStore';

export interface CanvasUpdateData {
  type: 'canvas_update' | 'potential_canvas_update';
  canvas_type?: 'workflow' | 'agent';
  yaml_content?: string;
  content?: string;
  message: string;
  task_id?: string;
  agent_name?: string;
}

export interface CanvasUpdateResult {
  success: boolean;
  message: string;
  canvas_type?: 'workflow' | 'agent';
  nodes_updated?: number;
  edges_updated?: number;
}

class CanvasUpdateService {
  /**
   * Process a canvas update from a WebSocket execution update
   */
  processCanvasUpdate(updateData: CanvasUpdateData): CanvasUpdateResult {
    console.log('🎨 Processing canvas update:', updateData);

    try {
      // Handle confirmed canvas updates
      if (updateData.type === 'canvas_update' && updateData.yaml_content) {
        return this.applyCanvasUpdate(updateData.yaml_content, updateData.canvas_type || 'workflow');
      }
      
      // Handle potential canvas updates (needs validation)
      if (updateData.type === 'potential_canvas_update' && updateData.content) {
        if (isValidYAML(updateData.content)) {
          // Determine canvas type from content
          const canvasType = this.detectCanvasType(updateData.content);
          return this.applyCanvasUpdate(updateData.content, canvasType);
        } else {
          return {
            success: false,
            message: 'Content does not appear to be valid YAML for canvas update'
          };
        }
      }

      return {
        success: false,
        message: 'No valid canvas data found in update'
      };

    } catch (error) {
      console.error('❌ Error processing canvas update:', error);
      return {
        success: false,
        message: `Error processing canvas update: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Apply a canvas update to the appropriate designer
   */
  private applyCanvasUpdate(yamlContent: string, canvasType: 'workflow' | 'agent'): CanvasUpdateResult {
    console.log(`🎨 Applying ${canvasType} canvas update with YAML:`, yamlContent.substring(0, 200) + '...');

    const parsedWorkflow = parseYAMLWorkflow(yamlContent);
    if (!parsedWorkflow) {
      return {
        success: false,
        message: 'Failed to parse YAML content'
      };
    }

    console.log('📋 Parsed workflow:', parsedWorkflow);

    // Convert to ReactFlow format based on canvas type
    let reactFlowData;
    if (canvasType === 'agent') {
      reactFlowData = convertToAgentFlowData(parsedWorkflow);
    } else {
      reactFlowData = convertToReactFlowData(parsedWorkflow);
    }

    console.log('🔄 Converted ReactFlow data:', reactFlowData);

    // Update the appropriate store
    const { setWorkflowData, setAgentData } = useAppStore.getState();
    
    if (canvasType === 'agent') {
      setAgentData(reactFlowData);
      console.log('✅ Updated agent designer canvas');
    } else {
      setWorkflowData(reactFlowData);
      console.log('✅ Updated workflow designer canvas');
    }

    return {
      success: true,
      message: `Successfully updated ${canvasType} canvas`,
      canvas_type: canvasType,
      nodes_updated: reactFlowData.nodes.length,
      edges_updated: reactFlowData.edges.length
    };
  }

  /**
   * Detect canvas type from YAML content
   */
  private detectCanvasType(content: string): 'workflow' | 'agent' {
    const lowerContent = content.toLowerCase();
    
    // Agent-specific keywords
    const agentKeywords = ['role:', 'skills:', 'department:', 'agent', 'supervisor', 'coordinator', 'specialist'];
    const agentScore = agentKeywords.filter(keyword => lowerContent.includes(keyword)).length;
    
    // Workflow-specific keywords
    const workflowKeywords = ['workflow', 'process', 'step', 'task', 'action'];
    const workflowScore = workflowKeywords.filter(keyword => lowerContent.includes(keyword)).length;
    
    // Return type with higher score, default to workflow
    return agentScore > workflowScore ? 'agent' : 'workflow';
  }

  /**
   * Validate and preview canvas update without applying
   */
  previewCanvasUpdate(yamlContent: string): CanvasUpdateResult & { 
    preview?: { nodes: Node[], edges: Edge[] } 
  } {
    try {
      const parsedWorkflow = parseYAMLWorkflow(yamlContent);
      if (!parsedWorkflow) {
        return {
          success: false,
          message: 'Invalid YAML format'
        };
      }

      const canvasType = this.detectCanvasType(yamlContent);
      const reactFlowData = canvasType === 'agent' 
        ? convertToAgentFlowData(parsedWorkflow)
        : convertToReactFlowData(parsedWorkflow);

      return {
        success: true,
        message: `Valid ${canvasType} canvas data`,
        canvas_type: canvasType,
        nodes_updated: reactFlowData.nodes.length,
        edges_updated: reactFlowData.edges.length,
        preview: reactFlowData
      };
    } catch (error) {
      return {
        success: false,
        message: `Preview error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Clear canvas data
   */
  clearCanvas(canvasType: 'workflow' | 'agent'): void {
    const { setWorkflowData, setAgentData } = useAppStore.getState();
    
    const emptyData = { nodes: [], edges: [] };
    
    if (canvasType === 'agent') {
      setAgentData(emptyData);
    } else {
      setWorkflowData(emptyData);
    }
    
    console.log(`🗑️ Cleared ${canvasType} canvas`);
  }
}

// Export singleton instance
export const canvasUpdateService = new CanvasUpdateService();

// Export types
export type { CanvasUpdateData, CanvasUpdateResult };