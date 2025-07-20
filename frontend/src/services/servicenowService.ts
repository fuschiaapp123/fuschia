import api from '@/utils/api';

export interface ServiceNowTable {
  label: string;
  name: string;
  primary: string;
}

export interface ServiceNowColumn {
  element: string;
  column_label: string;
}

export interface ServiceNowConnectionStatus {
  connected: boolean;
  message: string;
  instance_url?: string;
  tables_count?: number;
}

export interface ServiceNowTablesResponse {
  tables: ServiceNowTable[];
}

export interface ServiceNowColumnsResponse {
  columns: ServiceNowColumn[];
}

export interface ServiceNowRecordsResponse {
  records: Record<string, any>[];
  total?: number;
  page?: number;
  size?: number;
}

export interface ServiceNowExportRequest {
  table: string;
  fields?: string;
  filters?: string;
  limit?: number;
}

export interface ServiceNowExportResponse {
  message: string;
  exported_count: number;
  table_name: string;
}

export class ServiceNowService {
  /**
   * Simple login function for testing
   */
  static async testLogin(email: string, password: string): Promise<{ success: boolean; token?: string; error?: string }> {
    try {
      console.log('Attempting login for:', email);
      
      // Use form data as required by the OAuth2PasswordRequestForm
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      
      const baseUrl = api.defaults.baseURL || 'http://localhost:8000/api/v1';
      const loginUrl = baseUrl + '/auth/login';
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login successful:', data);
        return { success: true, token: data.access_token };
      } else {
        const errorData = await response.json();
        console.error('Login failed:', errorData);
        return { success: false, error: errorData.detail || 'Login failed' };
      }
    } catch (error: any) {
      console.error('Login error:', error);
      return { success: false, error: error.message || 'Network error' };
    }
  }
  /**
   * Test basic API connectivity (no auth required)
   */
  static async testApiConnectivity(): Promise<boolean> {
    try {
      console.log('Testing basic API connectivity...');
      
      // Get the base URL and construct the health endpoint correctly
      const baseUrl = api.defaults.baseURL || 'http://localhost:8000/api/v1'; // This is http://localhost:8000/api/v1
      const healthUrl = baseUrl.replace('/api/v1', '/health'); // This becomes http://localhost:8000/health
      console.log('Health check URL:', healthUrl);
      
      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      console.log('API connectivity test result:', response.status, data);
      return response.status === 200;
    } catch (error: any) {
      console.error('API connectivity test failed:', error);
      return false;
    }
  }

  /**
   * Check current authentication status by calling a protected endpoint
   */
  static async checkAuthStatus(): Promise<{ authenticated: boolean; error?: string }> {
    try {
      console.log('Checking authentication status...');
      console.log('Full API URL will be:', `${api.defaults.baseURL}/users/me`);
      
      // Let's also check what headers are being sent
      const authHeader = api.defaults.headers.common?.Authorization || 'Not set';
      console.log('Authorization header:', authHeader === 'Not set' ? 'Not set' : 'Bearer [token present]');
      
      const response = await api.get('/users/me');
      console.log('Auth check successful:', response.status, response.data);
      return { authenticated: true };
    } catch (error: any) {
      console.error('Auth check failed:', error);
      console.error('Full error object:', {
        message: error?.message,
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        config: {
          url: error?.config?.url,
          method: error?.config?.method,
          headers: error?.config?.headers
        }
      });
      return { 
        authenticated: false, 
        error: error?.response?.data?.detail || error?.message || 'Authentication failed'
      };
    }
  }

  /**
   * Check ServiceNow connection status
   */
  static async getConnectionStatus(): Promise<ServiceNowConnectionStatus> {
    try {
      console.log('Making API request to /servicenow/connection-status');
      console.log('API Base URL:', api.defaults.baseURL);
      
      const response = await api.get<ServiceNowConnectionStatus>('/servicenow/connection-status');
      console.log('ServiceNow connection status response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get ServiceNow connection status:', error);
      console.error('Error details:', {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        message: error?.message
      });
      
      // Check if it's an authentication error
      if (error?.response?.status === 401) {
        return {
          connected: false,
          message: 'Authentication failed - please log in again'
        };
      }
      
      return {
        connected: false,
        message: `Failed to check connection status: ${error?.response?.data?.detail || error?.message || 'Unknown error'}`
      };
    }
  }

  /**
   * Get available ServiceNow tables
   */
  static async getTables(): Promise<ServiceNowTable[]> {
    try {
      const response = await api.get<ServiceNowTablesResponse>('/servicenow/tables');
      return response.data.tables;
    } catch (error) {
      console.error('Failed to fetch ServiceNow tables:', error);
      throw new Error('Failed to fetch ServiceNow tables');
    }
  }

  /**
   * Get columns for a specific ServiceNow table
   */
  static async getTableColumns(tableName: string): Promise<ServiceNowColumn[]> {
    try {
      const response = await api.get<ServiceNowColumnsResponse>('/servicenow/columns', {
        params: { table: tableName }
      });
      return response.data.columns;
    } catch (error) {
      console.error(`Failed to fetch columns for table ${tableName}:`, error);
      throw new Error(`Failed to fetch columns for table ${tableName}`);
    }
  }

  /**
   * Get records from a ServiceNow table
   */
  static async getTableRecords(
    tableName: string,
    options: {
      page?: number;
      size?: number;
      sortField?: string;
      sortOrder?: 'asc' | 'desc';
      filters?: string;
      fields?: string;
    } = {}
  ): Promise<ServiceNowRecordsResponse> {
    try {
      const params: Record<string, any> = {
        table: tableName,
        page: options.page || 1,
        size: options.size || 10,
        ...options
      };

      if (options.sortField) {
        params.sort_field = options.sortField;
      }
      if (options.sortOrder) {
        params.sort_order = options.sortOrder;
      }
      if (options.filters) {
        params.filters = options.filters;
      }
      if (options.fields) {
        params.fields = options.fields;
      }

      const response = await api.get<ServiceNowRecordsResponse>('/servicenow/records', {
        params
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch records from table ${tableName}:`, error);
      throw new Error(`Failed to fetch records from table ${tableName}`);
    }
  }

  /**
   * Export ServiceNow table data to Neo4j
   */
  static async exportTableToNeo4j(exportRequest: ServiceNowExportRequest): Promise<ServiceNowExportResponse> {
    try {
      const response = await api.post<ServiceNowExportResponse>('/servicenow/export', exportRequest);
      return response.data;
    } catch (error) {
      console.error(`Failed to export table ${exportRequest.table}:`, error);
      throw new Error(`Failed to export table ${exportRequest.table}`);
    }
  }
}

export default ServiceNowService;