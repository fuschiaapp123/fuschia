import React, { useState, useCallback, useEffect } from 'react';
import { 
  Database, 
  RefreshCw, 
  Eye, 
  CheckCircle,
  AlertCircle,
  ChevronRight,
  Search,
  Upload
} from 'lucide-react';
import ServiceNowService, { ServiceNowColumn } from '@/services/servicenowService';
import { useAuthStore } from '@/store/authStore';

interface DataSource {
  id: string;
  name: string;
  type: 'ServiceNow' | 'Salesforce' | 'JIRA' | 'SharePoint' | 'SQL Server' | 'Oracle';
  status: 'connected' | 'disconnected' | 'error';
  lastSync: string;
  description: string;
  icon: string;
}

interface DataTable {
  name: string;
  displayName: string;
  recordCount?: number;
  lastUpdated?: string;
  description?: string;
  fields: ServiceNowColumn[];
  primary: string;
}

interface TableData {
  [key: string]: any;
}


export const DataImport: React.FC = () => {
  // Auth state
  const { isAuthenticated, token, user, login } = useAuthStore();
  
  // Data Sources State - Initially just ServiceNow
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);
  
  // Component State
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [selectedTable, setSelectedTable] = useState<DataTable | null>(null);
  const [availableTables, setAvailableTables] = useState<DataTable[]>([]);
  const [tableData, setTableData] = useState<TableData[]>([]);
  
  // Loading States
  const [isLoadingTables, setIsLoadingTables] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  
  // UI State
  const [importStatus, setImportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [searchTerm, setSearchTerm] = useState('');
  const [tableSearchTerm, setTableSearchTerm] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  
  // Login form state
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const addDebugInfo = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setDebugInfo(prev => [...prev, `[${timestamp}] ${message}`]);
    console.log(`[DataImport Debug] ${message}`);
  };

  const clearDebugInfo = () => {
    setDebugInfo([]);
  };

  const testServiceNowDebug = async () => {
    addDebugInfo('Testing ServiceNow debug endpoint...');
    
    try {
      const response = await fetch('/api/v1/servicenow/debug-connection', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      addDebugInfo(`Debug Response: ${JSON.stringify(result, null, 2)}`);
      
      if (result.status === 'success') {
        addDebugInfo(`✅ HTTP Status: ${result.http_status}`);
        addDebugInfo(`✅ Content Type: ${result.content_type}`);
        addDebugInfo(`✅ JSON Valid: ${result.json_valid}`);
        if (result.json_keys) {
          addDebugInfo(`✅ JSON Keys: ${result.json_keys}`);
        }
      } else {
        addDebugInfo(`❌ Error: ${result.message}`);
        if (result.json_error) {
          addDebugInfo(`❌ JSON Error: ${result.json_error}`);
        }
      }
    } catch (error) {
      addDebugInfo(`❌ Debug test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    addDebugInfo(`Attempting login for: ${loginEmail}`);
    
    try {
      const result = await ServiceNowService.testLogin(loginEmail, loginPassword);
      
      if (result.success && result.token) {
        addDebugInfo('Login successful!');
        
        // Create a basic user object
        const userObj = {
          id: 'temp-user',
          email: loginEmail,
          full_name: loginEmail,
          is_active: true
        };
        
        // Update the auth store
        login(userObj, result.token);
        
        // Hide the login form
        setShowLoginForm(false);
        setLoginEmail('');
        setLoginPassword('');
        
        addDebugInfo('Auth store updated, reloading data sources...');
      } else {
        addDebugInfo(`Login failed: ${result.error}`);
        setErrorMessage(`Login failed: ${result.error}`);
      }
    } catch (error: any) {
      addDebugInfo(`Login error: ${error.message}`);
      setErrorMessage(`Login error: ${error.message}`);
    } finally {
      setIsLoggingIn(false);
    }
  };

  // Load ServiceNow connection status and initialize data sources
  useEffect(() => {
    const loadDataSources = async () => {
      try {
        addDebugInfo('Starting data source loading...');
        setIsLoadingSources(true);
        setErrorMessage(null);
        
        // Check authentication first
        addDebugInfo(`Auth check: isAuthenticated=${isAuthenticated}, hasToken=${!!token}`);
        if (!isAuthenticated || !token) {
          const errorMsg = 'Please log in to access data sources';
          addDebugInfo(`Auth failed: ${errorMsg}`);
          setErrorMessage(errorMsg);
          setDataSources([]);
          setIsLoadingSources(false);
          return;
        }
        
        // Log token details for debugging (first/last 10 chars only for security)
        if (token) {
          const tokenPreview = token.length > 20 ? 
            `${token.substring(0, 10)}...${token.substring(token.length - 10)}` : 
            token;
          addDebugInfo(`Token preview: ${tokenPreview}`);
        }
        
        addDebugInfo(`User: ${user?.email || 'unknown'}`);
        
        // Test basic API connectivity first
        addDebugInfo('Testing API connectivity...');
        try {
          const apiConnected = await ServiceNowService.testApiConnectivity();
          addDebugInfo(`API connectivity: ${apiConnected ? 'SUCCESS' : 'FAILED'}`);
          if (!apiConnected) {
            addDebugInfo('API connectivity failed, but continuing anyway...');
          }
        } catch (connError: any) {
          addDebugInfo(`API connectivity test error: ${connError.message}`);
        }
        
        // Check authentication status with the API
        addDebugInfo('Checking auth status with API...');
        try {
          const authStatus = await ServiceNowService.checkAuthStatus();
          addDebugInfo(`Auth status: ${authStatus.authenticated ? 'SUCCESS' : 'FAILED'} - ${authStatus.error || 'OK'}`);
          if (!authStatus.authenticated) {
            addDebugInfo(`Auth failed: ${authStatus.error}, but continuing to test ServiceNow...`);
          }
        } catch (authError: any) {
          addDebugInfo(`Auth check error: ${authError.message}`);
        }
        
        addDebugInfo('Getting ServiceNow connection status...');
        const connectionStatus = await ServiceNowService.getConnectionStatus();
        addDebugInfo(`ServiceNow status: ${connectionStatus.connected ? 'CONNECTED' : 'DISCONNECTED'} - ${connectionStatus.message}`);
        
        const serviceNowSource: DataSource = {
          id: 'servicenow-prod',
          name: 'ServiceNow Production',
          type: 'ServiceNow',
          status: connectionStatus.connected ? 'connected' : 'error',
          lastSync: connectionStatus.connected ? 'Just now' : 'Failed',
          description: connectionStatus.message,
          icon: '🔧'
        };
        
        // For now, only ServiceNow is implemented
        setDataSources([serviceNowSource]);
        addDebugInfo('Data sources loaded successfully');
        setErrorMessage(null);
      } catch (error: any) {
        const errorMsg = `Failed to load data sources: ${error?.message || 'Unknown error'}`;
        addDebugInfo(`ERROR: ${errorMsg}`);
        console.error('Failed to load data sources:', error);
        setErrorMessage(errorMsg);
        
        // Fallback data source with error status
        const fallbackSource: DataSource = {
          id: 'servicenow-prod',
          name: 'ServiceNow Production',
          type: 'ServiceNow',
          status: 'error',
          lastSync: 'Failed',
          description: 'Unable to connect to ServiceNow',
          icon: '🔧'
        };
        setDataSources([fallbackSource]);
      } finally {
        setIsLoadingSources(false);
      }
    };
    
    loadDataSources();
  }, [isAuthenticated, token]); // Re-run when authentication state changes

  const handleSourceSelect = useCallback(async (source: DataSource) => {
    if (source.status !== 'connected') {
      setErrorMessage('Cannot select disconnected data source');
      return;
    }
    
    setSelectedSource(source);
    setSelectedTable(null);
    setTableData([]);
    setAvailableTables([]);
    setIsLoadingTables(true);
    setErrorMessage(null);
    
    try {
      if (source.type === 'ServiceNow') {
        // Fetch actual ServiceNow tables
        const tables = await ServiceNowService.getTables();
        
        // Convert ServiceNow tables to DataTable format
        const dataTablePromises = tables.map(async (table) => {
          return {
                name: table.name,
                displayName: table.label,
                fields: [],
                primary: table.primary,
                description: `ServiceNow ${table.label} table`,
                lastUpdated: 'Live data',
                recordCount: undefined // We'll fetch this when needed
              } as DataTable;
          // try {
          //   const columns = await ServiceNowService.getTableColumns(table.name);
          //   return {
          //     name: table.name,
          //     displayName: table.label,
          //     fields: columns,
          //     primary: table.primary,
          //     description: `ServiceNow ${table.label} table`,
          //     lastUpdated: 'Live data',
          //     recordCount: undefined // We'll fetch this when needed
          //   } as DataTable;
          // } catch (error) {
          //   console.error(`Failed to fetch columns for table ${table.name}:`, error);
          //   return {
          //     name: table.name,
          //     displayName: table.label,
          //     fields: [],
          //     primary: table.primary,
          //     description: `ServiceNow ${table.label} table`,
          //     lastUpdated: 'Live data'
          //   } as DataTable;
          // }
        });
        
        const dataTables = await Promise.all(dataTablePromises);
        setAvailableTables(dataTables);
      }
    } catch (error) {
      console.error('Failed to fetch tables:', error);
      setErrorMessage('Failed to fetch tables from data source');
    } finally {
      setIsLoadingTables(false);
    }
  }, []);

  const handleTableSelect = useCallback(async (table: DataTable) => {
    setSelectedTable(table);
    setIsLoadingData(true);
    setErrorMessage(null);
    
    try {
      if (selectedSource?.type === 'ServiceNow') {
        // Fetch actual data from ServiceNow
        const response = await ServiceNowService.getTableRecords(table.name, {
          size: 10, // Preview only 10 records
          page: 1
        });
        
        setTableData(response.records);
        
        // Update table with actual record count if available
        if (response.total) {
          const updatedTable = { ...table, recordCount: response.total };
          setSelectedTable(updatedTable);
        }
      }
    } catch (error) {
      console.error('Failed to fetch table data:', error);
      setErrorMessage('Failed to fetch table data');
      setTableData([]);
    } finally {
      setIsLoadingData(false);
    }
  }, [selectedSource]);

  const handleImportData = useCallback(async () => {
    if (!selectedSource || !selectedTable) return;
    
    setIsImporting(true);
    setImportStatus('idle');
    setErrorMessage(null);
    
    try {
      if (selectedSource.type === 'ServiceNow') {
        // Export to Neo4j using the real API
        const exportResponse = await ServiceNowService.exportTableToNeo4j({
          table: selectedTable.name,
          limit: 1000 // Export up to 1000 records
        });
        
        console.log('Export successful:', exportResponse);
        setImportStatus('success');
      }
    } catch (error) {
      console.error('Import failed:', error);
      setErrorMessage('Failed to import data to knowledge graph');
      setImportStatus('error');
    } finally {
      setIsImporting(false);
    }
  }, [selectedSource, selectedTable]);

  const handleRefreshSources = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setErrorMessage('Please log in to refresh data sources');
      return;
    }
    
    setIsLoadingSources(true);
    setErrorMessage(null);
    
    try {
      const connectionStatus = await ServiceNowService.getConnectionStatus();
      
      const serviceNowSource: DataSource = {
        id: 'servicenow-prod',
        name: 'ServiceNow Production',
        type: 'ServiceNow',
        status: connectionStatus.connected ? 'connected' : 'error',
        lastSync: connectionStatus.connected ? 'Just now' : 'Failed',
        description: connectionStatus.message,
        icon: '🔧'
      };
      
      setDataSources([serviceNowSource]);
    } catch (error) {
      console.error('Failed to refresh data sources:', error);
      setErrorMessage('Failed to refresh data sources');
    } finally {
      setIsLoadingSources(false);
    }
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'disconnected':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'disconnected':
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  const filteredSources = dataSources.filter(source =>
    source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    source.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTables = availableTables.filter(table =>
    table.name.toLowerCase().includes(tableSearchTerm.toLowerCase()) ||
    table.displayName.toLowerCase().includes(tableSearchTerm.toLowerCase()) ||
    (table.description && table.description.toLowerCase().includes(tableSearchTerm.toLowerCase()))
  );

  // Show authentication required message if not logged in
  if (!isAuthenticated) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Import</h2>
          <p className="text-gray-600">Import data from connected systems into the knowledge graph</p>
        </div>
        
        {/* Debug Panel for unauthenticated users */}
        {debugInfo.length > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Debug Information</h4>
              <button 
                onClick={clearDebugInfo}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
            <div className="max-h-40 overflow-y-auto">
              {debugInfo.map((info, index) => (
                <div key={index} className="text-xs font-mono text-gray-600 mb-1">
                  {info}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {!showLoginForm ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-yellow-900 mb-2">Authentication Required</h3>
            <p className="text-yellow-700 mb-4">Please log in to access data import features.</p>
            <div className="space-x-3">
              <button 
                onClick={() => setShowLoginForm(true)}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
              >
                Login Here
              </button>
              <button 
                onClick={() => window.location.href = '/login'}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                Go to Login Page
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Login</h3>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  required
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  disabled={isLoggingIn}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 transition-colors"
                >
                  {isLoggingIn ? 'Logging in...' : 'Login'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowLoginForm(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Import</h2>
        <p className="text-gray-600">Import data from connected systems into the knowledge graph</p>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <div>
              <h4 className="font-medium text-red-900">Error</h4>
              <p className="text-sm text-red-700">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Debug Panel */}
      {debugInfo.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Debug Information</h4>
            <div className="flex space-x-2">
              <button 
                onClick={testServiceNowDebug}
                className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
              >
                Test Debug Endpoint
              </button>
              <button 
                onClick={clearDebugInfo}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
          </div>
          <div className="max-h-40 overflow-y-auto">
            {debugInfo.map((info, index) => (
              <div key={index} className="text-xs font-mono text-gray-600 mb-1">
                {info}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Debug Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Debug Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button 
            onClick={testServiceNowDebug}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            <span>🔍</span>
            <span>Test ServiceNow Debug</span>
          </button>
          <button 
            onClick={clearDebugInfo}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
          >
            <span>🧹</span>
            <span>Clear Debug Info</span>
          </button>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className={`flex items-center space-x-2 ${selectedSource ? 'text-fuschia-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${selectedSource ? 'bg-fuschia-100' : 'bg-gray-100'}`}>
              <span className="text-sm font-medium">1</span>
            </div>
            <span className="font-medium">Select Data Source</span>
          </div>
          
          <ChevronRight className="w-5 h-5 text-gray-400" />
          
          <div className={`flex items-center space-x-2 ${selectedTable ? 'text-fuschia-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${selectedTable ? 'bg-fuschia-100' : 'bg-gray-100'}`}>
              <span className="text-sm font-medium">2</span>
            </div>
            <span className="font-medium">Select Table</span>
          </div>
          
          <ChevronRight className="w-5 h-5 text-gray-400" />
          
          <div className={`flex items-center space-x-2 ${tableData.length > 0 ? 'text-fuschia-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${tableData.length > 0 ? 'bg-fuschia-100' : 'bg-gray-100'}`}>
              <span className="text-sm font-medium">3</span>
            </div>
            <span className="font-medium">Browse Data</span>
          </div>
          
          <ChevronRight className="w-5 h-5 text-gray-400" />
          
          <div className={`flex items-center space-x-2 ${importStatus === 'success' ? 'text-green-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${importStatus === 'success' ? 'bg-green-100' : 'bg-gray-100'}`}>
              <span className="text-sm font-medium">4</span>
            </div>
            <span className="font-medium">Import to Graph</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1: Data Sources */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Data Sources</h3>
              <button 
                onClick={handleRefreshSources}
                disabled={isLoadingSources}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoadingSources ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="mt-3">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search data sources..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                />
              </div>
            </div>
          </div>
          
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {isLoadingSources && (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-3 animate-spin" />
                <p className="text-gray-500">Loading data sources...</p>
              </div>
            )}
            
            {!isLoadingSources && filteredSources.map((source) => (
              <div
                key={source.id}
                onClick={() => handleSourceSelect(source)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedSource?.id === source.id
                    ? 'border-fuschia-300 bg-fuschia-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{source.icon}</span>
                    <div>
                      <h4 className="font-medium text-gray-900">{source.name}</h4>
                      <p className="text-xs text-gray-500">{source.type}</p>
                    </div>
                  </div>
                  {getStatusIcon(source.status)}
                </div>
                <div className="flex items-center justify-between">
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(source.status)}`}>
                    {source.status}
                  </span>
                  <span className="text-xs text-gray-500">{source.lastSync}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 2: Tables */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Available Tables</h3>
            {selectedSource && (
              <p className="text-sm text-gray-600 mt-1">From {selectedSource.name}</p>
            )}
            {selectedSource && !isLoadingTables && availableTables.length > 0 && (
              <div className="mt-3">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search tables..."
                    value={tableSearchTerm}
                    onChange={(e) => setTableSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                  />
                </div>
              </div>
            )}
          </div>
          
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {!selectedSource && (
              <div className="text-center py-8">
                <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Select a data source to view tables</p>
              </div>
            )}
            
            {selectedSource && isLoadingTables && (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-3 animate-spin" />
                <p className="text-gray-500">Loading tables...</p>
              </div>
            )}
            
            {selectedSource && !isLoadingTables && filteredTables.length === 0 && availableTables.length > 0 && (
              <div className="text-center py-8">
                <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No tables match your search</p>
                <button 
                  onClick={() => setTableSearchTerm('')}
                  className="text-sm text-fuschia-600 hover:text-fuschia-700 mt-2"
                >
                  Clear search
                </button>
              </div>
            )}
            
            {selectedSource && !isLoadingTables && filteredTables.map((table) => (
              <div
                key={table.name}
                onClick={() => handleTableSelect(table)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedTable?.name === table.name
                    ? 'border-fuschia-300 bg-fuschia-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{table.displayName}</h4>
                  <span className="text-sm text-gray-500">
                    {table.recordCount ? `${table.recordCount.toLocaleString()} records` : 'Live data'}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-2">{table.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Updated {table.lastUpdated}</span>
                  <div className="flex items-center space-x-1">
                    <Eye className="w-3 h-3 text-gray-400" />
                    <span className="text-xs text-gray-400">{table.fields.length} fields</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step 3: Data Preview */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Data Preview</h3>
              {selectedTable && tableData.length > 0 && (
                <button
                  onClick={handleImportData}
                  disabled={isImporting}
                  className="flex items-center space-x-2 px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  {isImporting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Importing...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Import to Graph</span>
                    </>
                  )}
                </button>
              )}
            </div>
            {selectedTable && (
              <p className="text-sm text-gray-600 mt-1">Sample data from {selectedTable.displayName}</p>
            )}
          </div>
          
          <div className="p-4 max-h-96 overflow-auto">
            {!selectedTable && (
              <div className="text-center py-8">
                <Eye className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Select a table to preview data</p>
              </div>
            )}
            
            {selectedTable && isLoadingData && (
              <div className="text-center py-8">
                <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-3 animate-spin" />
                <p className="text-gray-500">Loading data...</p>
              </div>
            )}
            
            {selectedTable && !isLoadingData && tableData.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      {Object.keys(tableData[0]).map((field) => (
                        <th key={field} className="text-left py-2 px-3 font-medium text-gray-700">
                          {field}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.slice(0, 10).map((row, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="py-2 px-3 text-gray-900">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {tableData.length > 10 && (
                  <div className="mt-3 text-center">
                    <p className="text-xs text-gray-500">
                      Showing 10 of {tableData.length} records. Full dataset will be imported.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Import Status */}
      {importStatus !== 'idle' && (
        <div className={`p-4 rounded-lg border ${
          importStatus === 'success' 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center space-x-3">
            {importStatus === 'success' ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600" />
            )}
            <div>
              <h4 className={`font-medium ${
                importStatus === 'success' ? 'text-green-900' : 'text-red-900'
              }`}>
                {importStatus === 'success' ? 'Import Successful' : 'Import Failed'}
              </h4>
              <p className={`text-sm ${
                importStatus === 'success' ? 'text-green-700' : 'text-red-700'
              }`}>
                {importStatus === 'success' 
                  ? `Successfully imported ${tableData.length} records from ${selectedTable?.displayName} into the knowledge graph.`
                  : 'There was an error importing the data. Please try again or contact support.'
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};