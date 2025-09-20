/**
 * MCP (Model Context Protocol) Client Service
 * Handles communication with MCP servers and tools from the frontend
 */

interface MCPServer {
  id: string;
  name: string;
  description?: string;
  command: string;
  args: string[];
  capabilities: {
    tools: boolean;
    resources: boolean;
    prompts: boolean;
  };
  status: 'active' | 'inactive' | 'error';
  auto_start: boolean;
  process_id?: string;
  last_error?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface MCPTool {
  id: string;
  server_id: string;
  tool_name: string;
  description?: string;
  input_schema: any;
  fuschia_tool_id?: string;
  is_active: boolean;
  categories: string[];
  version: string;
  created_at: string;
}

interface MCPResource {
  id: string;
  server_id: string;
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
  is_active: boolean;
  last_accessed?: string;
  created_at: string;
}

interface MCPToolExecution {
  execution_id: string;
  tool_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  execution_time_ms?: number;
}

interface MCPToolExecutionRequest {
  tool_name: string;
  arguments: Record<string, any>;
  agent_id?: string;
  workflow_execution_id?: string;
  context_data?: Record<string, any>;
}

interface MCPServerConfig {
  id?: string;
  name: string;
  description?: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  capabilities?: {
    tools: boolean;
    resources: boolean;
    prompts: boolean;
  };
  auto_start?: boolean;
}

class MCPClientService {
  private readonly baseUrl = '/api/v1/mcp';
  private cache = new Map<string, any>();
  private cacheExpiry = new Map<string, number>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Create authenticated headers for API requests
   */
  private createAuthHeaders(): Headers {
    const headers = new Headers();
    headers.append('Content-Type', 'application/json');
    
    // Get token from localStorage or auth store
    const token = localStorage.getItem('auth_token'); // Adjust based on your auth implementation
    if (token) {
      headers.append('Authorization', `Bearer ${token}`);
    }
    
    return headers;
  }

  /**
   * Cache helper methods
   */
  private getCachedData(key: string): any | null {
    const expiry = this.cacheExpiry.get(key);
    if (expiry && Date.now() > expiry) {
      this.cache.delete(key);
      this.cacheExpiry.delete(key);
      return null;
    }
    return this.cache.get(key) || null;
  }

  private setCachedData(key: string, data: any): void {
    this.cache.set(key, data);
    this.cacheExpiry.set(key, Date.now() + this.CACHE_TTL);
  }

  /**
   * MCP Server Management
   */

  async createServer(config: MCPServerConfig): Promise<MCPServer> {
    try {
      const response = await fetch(`${this.baseUrl}/servers`, {
        method: 'POST',
        headers: this.createAuthHeaders(),
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`Failed to create MCP server: ${response.status} ${response.statusText}`);
      }

      const server = await response.json();
      
      // Clear cache
      this.cache.delete('servers');
      
      return server;
    } catch (error) {
      console.error('Error creating MCP server:', error);
      throw error;
    }
  }

  async listServers(useCache = true): Promise<MCPServer[]> {
    try {
      const cacheKey = 'servers';
      
      if (useCache) {
        const cached = this.getCachedData(cacheKey);
        if (cached) return cached;
      }

      const response = await fetch(`${this.baseUrl}/servers`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to list MCP servers: ${response.status} ${response.statusText}`);
      }

      const servers = await response.json();
      
      if (useCache) {
        this.setCachedData(cacheKey, servers);
      }
      
      return servers;
    } catch (error) {
      console.error('Error listing MCP servers:', error);
      throw error;
    }
  }

  async getServer(serverId: string): Promise<MCPServer> {
    try {
      const response = await fetch(`${this.baseUrl}/servers/${serverId}`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get MCP server: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting MCP server:', error);
      throw error;
    }
  }

  async startServer(serverId: string): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/servers/${serverId}/start`, {
        method: 'POST',
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to start MCP server: ${response.status} ${response.statusText}`);
      }

      // Clear cache
      this.cache.delete('servers');
      this.cache.delete(`server_${serverId}`);

      return await response.json();
    } catch (error) {
      console.error('Error starting MCP server:', error);
      throw error;
    }
  }

  async stopServer(serverId: string): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/servers/${serverId}/stop`, {
        method: 'POST',
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to stop MCP server: ${response.status} ${response.statusText}`);
      }

      // Clear cache
      this.cache.delete('servers');
      this.cache.delete(`server_${serverId}`);

      return await response.json();
    } catch (error) {
      console.error('Error stopping MCP server:', error);
      throw error;
    }
  }

  async deleteServer(serverId: string): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/servers/${serverId}`, {
        method: 'DELETE',
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to delete MCP server: ${response.status} ${response.statusText}`);
      }

      // Clear cache
      this.cache.delete('servers');
      this.cache.delete(`server_${serverId}`);

      return await response.json();
    } catch (error) {
      console.error('Error deleting MCP server:', error);
      throw error;
    }
  }

  /**
   * MCP Tools Management
   */

  async listTools(serverId: string, useCache = true): Promise<MCPTool[]> {
    try {
      const cacheKey = `tools_${serverId}`;
      
      if (useCache) {
        const cached = this.getCachedData(cacheKey);
        if (cached) return cached;
      }

      const response = await fetch(`${this.baseUrl}/servers/${serverId}/tools`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to list MCP tools: ${response.status} ${response.statusText}`);
      }

      const tools = await response.json();
      
      if (useCache) {
        this.setCachedData(cacheKey, tools);
      }
      
      return tools;
    } catch (error) {
      console.error('Error listing MCP tools:', error);
      throw error;
    }
  }

  async executeTool(request: MCPToolExecutionRequest): Promise<MCPToolExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/tools/execute`, {
        method: 'POST',
        headers: this.createAuthHeaders(),
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`Failed to execute MCP tool: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing MCP tool:', error);
      throw error;
    }
  }

  async getToolExecutions(options: {
    agent_id?: string;
    status?: string;
    limit?: number;
  } = {}): Promise<MCPToolExecution[]> {
    try {
      const params = new URLSearchParams();
      if (options.agent_id) params.append('agent_id', options.agent_id);
      if (options.status) params.append('status', options.status);
      if (options.limit) params.append('limit', options.limit.toString());

      const response = await fetch(`${this.baseUrl}/tools/executions?${params.toString()}`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get tool executions: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting tool executions:', error);
      throw error;
    }
  }

  async getToolExecution(executionId: string): Promise<MCPToolExecution> {
    try {
      const response = await fetch(`${this.baseUrl}/tools/executions/${executionId}`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get tool execution: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting tool execution:', error);
      throw error;
    }
  }

  /**
   * MCP Resources Management
   */

  async listResources(serverId: string, useCache = true): Promise<MCPResource[]> {
    try {
      const cacheKey = `resources_${serverId}`;
      
      if (useCache) {
        const cached = this.getCachedData(cacheKey);
        if (cached) return cached;
      }

      const response = await fetch(`${this.baseUrl}/servers/${serverId}/resources`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to list MCP resources: ${response.status} ${response.statusText}`);
      }

      const resources = await response.json();
      
      if (useCache) {
        this.setCachedData(cacheKey, resources);
      }
      
      return resources;
    } catch (error) {
      console.error('Error listing MCP resources:', error);
      throw error;
    }
  }

  async readResource(serverId: string, resourceUri: string): Promise<any> {
    try {
      const encodedUri = encodeURIComponent(resourceUri);
      const response = await fetch(`${this.baseUrl}/servers/${serverId}/resources/${encodedUri}`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to read MCP resource: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error reading MCP resource:', error);
      throw error;
    }
  }

  /**
   * Status and Health
   */

  async getStatus(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/status`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get MCP status: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting MCP status:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        headers: this.createAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to check MCP health: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking MCP health:', error);
      throw error;
    }
  }

  /**
   * Utility Methods
   */

  clearCache(): void {
    this.cache.clear();
    this.cacheExpiry.clear();
  }

  /**
   * Validate tool arguments against schema
   */
  validateToolArguments(tool: MCPTool, arguments: Record<string, any>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    const schema = tool.input_schema;

    if (!schema || !schema.properties) {
      return { valid: true, errors: [] };
    }

    // Check required fields
    const required = schema.required || [];
    for (const field of required) {
      if (!(field in arguments)) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    // Basic type checking
    for (const [field, value] of Object.entries(arguments)) {
      const fieldSchema = schema.properties[field];
      if (fieldSchema) {
        const expectedType = fieldSchema.type;
        const actualType = typeof value;
        
        if (expectedType === 'string' && actualType !== 'string') {
          errors.push(`Field '${field}' should be a string, got ${actualType}`);
        } else if (expectedType === 'number' && actualType !== 'number') {
          errors.push(`Field '${field}' should be a number, got ${actualType}`);
        } else if (expectedType === 'boolean' && actualType !== 'boolean') {
          errors.push(`Field '${field}' should be a boolean, got ${actualType}`);
        } else if (expectedType === 'array' && !Array.isArray(value)) {
          errors.push(`Field '${field}' should be an array, got ${actualType}`);
        } else if (expectedType === 'object' && (actualType !== 'object' || Array.isArray(value))) {
          errors.push(`Field '${field}' should be an object, got ${actualType}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Get default server configurations
   */
  getDefaultServerConfigs(): MCPServerConfig[] {
    return [
      {
        id: 'filesystem',
        name: 'File System',
        description: 'Access and manipulate files',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', '/tmp/mcp-files'],
        capabilities: { tools: true, resources: true, prompts: false },
        auto_start: false
      },
      {
        id: 'postgres',
        name: 'PostgreSQL Database',
        description: 'Query and manage PostgreSQL databases',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-postgres'],
        capabilities: { tools: true, resources: false, prompts: false },
        auto_start: false
      },
      {
        id: 'web',
        name: 'Web Browser',
        description: 'Browse and interact with web pages',
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-web'],
        capabilities: { tools: true, resources: true, prompts: false },
        auto_start: false
      }
    ];
  }
}

// Export singleton instance
export const mcpClientService = new MCPClientService();
export type { MCPServer, MCPTool, MCPResource, MCPToolExecution, MCPToolExecutionRequest, MCPServerConfig };