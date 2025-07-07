import React, { useState, useCallback } from 'react';
import { 
  Database, 
  RefreshCw, 
  Eye, 
  Download, 
  CheckCircle,
  AlertCircle,
  ChevronRight,
  Search,
  Filter,
  Upload
} from 'lucide-react';

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
  recordCount: number;
  lastUpdated: string;
  description: string;
  fields: string[];
}

interface TableData {
  [key: string]: any;
}

const dataSources: DataSource[] = [
  {
    id: 'servicenow-prod',
    name: 'ServiceNow Production',
    type: 'ServiceNow',
    status: 'connected',
    lastSync: '2 minutes ago',
    description: 'Production ServiceNow instance for incident and change management',
    icon: '🔧'
  },
  {
    id: 'salesforce-sales',
    name: 'Salesforce Sales Cloud',
    type: 'Salesforce',
    status: 'connected',
    lastSync: '5 minutes ago',
    description: 'Sales pipeline and customer relationship data',
    icon: '☁️'
  },
  {
    id: 'jira-dev',
    name: 'JIRA Development',
    type: 'JIRA',
    status: 'connected',
    lastSync: '10 minutes ago',
    description: 'Development project tracking and issue management',
    icon: '📋'
  },
  {
    id: 'sharepoint-docs',
    name: 'SharePoint Documents',
    type: 'SharePoint',
    status: 'disconnected',
    lastSync: '2 hours ago',
    description: 'Document library and collaboration platform',
    icon: '📄'
  },
  {
    id: 'sqlserver-hr',
    name: 'SQL Server HR Database',
    type: 'SQL Server',
    status: 'connected',
    lastSync: '1 hour ago',
    description: 'Human resources and employee data',
    icon: '🗄️'
  }
];

const mockTables: Record<string, DataTable[]> = {
  'servicenow-prod': [
    {
      name: 'incident',
      displayName: 'Incidents',
      recordCount: 15234,
      lastUpdated: '2 minutes ago',
      description: 'IT incident records and resolution tracking',
      fields: ['number', 'short_description', 'state', 'priority', 'assigned_to', 'opened_at', 'resolved_at']
    },
    {
      name: 'change_request',
      displayName: 'Change Requests',
      recordCount: 8756,
      lastUpdated: '5 minutes ago',
      description: 'Change management and approval workflow',
      fields: ['number', 'short_description', 'state', 'risk', 'requested_by', 'start_date', 'end_date']
    },
    {
      name: 'cmdb_ci',
      displayName: 'Configuration Items',
      recordCount: 45123,
      lastUpdated: '1 hour ago',
      description: 'Configuration management database items',
      fields: ['name', 'sys_class_name', 'serial_number', 'asset_tag', 'location', 'assigned_to']
    }
  ],
  'salesforce-sales': [
    {
      name: 'Account',
      displayName: 'Accounts',
      recordCount: 12456,
      lastUpdated: '3 minutes ago',
      description: 'Customer account information and details',
      fields: ['Name', 'Type', 'Industry', 'Annual_Revenue', 'Owner', 'Created_Date']
    },
    {
      name: 'Opportunity',
      displayName: 'Opportunities',
      recordCount: 8934,
      lastUpdated: '5 minutes ago',
      description: 'Sales opportunities and pipeline data',
      fields: ['Name', 'Stage', 'Amount', 'Close_Date', 'Probability', 'Account_Name']
    },
    {
      name: 'Contact',
      displayName: 'Contacts',
      recordCount: 23567,
      lastUpdated: '8 minutes ago',
      description: 'Contact information for prospects and customers',
      fields: ['Name', 'Email', 'Phone', 'Title', 'Account', 'Lead_Source']
    }
  ],
  'jira-dev': [
    {
      name: 'Issue',
      displayName: 'Issues',
      recordCount: 6789,
      lastUpdated: '10 minutes ago',
      description: 'Development tasks, bugs, and stories',
      fields: ['Key', 'Summary', 'Issue_Type', 'Status', 'Priority', 'Assignee', 'Reporter']
    },
    {
      name: 'Project',
      displayName: 'Projects',
      recordCount: 45,
      lastUpdated: '2 hours ago',
      description: 'Development projects and initiatives',
      fields: ['Key', 'Name', 'Lead', 'Category', 'Project_Type', 'Created']
    }
  ]
};

const mockTableData: Record<string, TableData[]> = {
  'servicenow-prod-incident': [
    { number: 'INC0010001', short_description: 'Email server down', state: 'In Progress', priority: 'High', assigned_to: 'John Doe', opened_at: '2024-01-15 09:30' },
    { number: 'INC0010002', short_description: 'Login issues with CRM', state: 'New', priority: 'Medium', assigned_to: 'Jane Smith', opened_at: '2024-01-15 10:15' },
    { number: 'INC0010003', short_description: 'Printer not working', state: 'Resolved', priority: 'Low', assigned_to: 'Bob Wilson', opened_at: '2024-01-15 11:00' },
    { number: 'INC0010004', short_description: 'Network connectivity issues', state: 'In Progress', priority: 'High', assigned_to: 'Alice Brown', opened_at: '2024-01-15 11:30' },
    { number: 'INC0010005', short_description: 'Software installation request', state: 'New', priority: 'Low', assigned_to: 'Charlie Davis', opened_at: '2024-01-15 12:00' }
  ],
  'salesforce-sales-Account': [
    { Name: 'Acme Corporation', Type: 'Customer', Industry: 'Technology', Annual_Revenue: '$5M', Owner: 'Sarah Johnson', Created_Date: '2023-06-15' },
    { Name: 'Global Solutions Inc', Type: 'Prospect', Industry: 'Consulting', Annual_Revenue: '$12M', Owner: 'Mike Chen', Created_Date: '2023-08-22' },
    { Name: 'TechStart Ltd', Type: 'Customer', Industry: 'Software', Annual_Revenue: '$2M', Owner: 'Lisa Park', Created_Date: '2023-09-10' },
    { Name: 'Enterprise Systems', Type: 'Partner', Industry: 'IT Services', Annual_Revenue: '$50M', Owner: 'David Kumar', Created_Date: '2023-10-05' },
    { Name: 'Innovation Labs', Type: 'Prospect', Industry: 'Research', Annual_Revenue: '$8M', Owner: 'Emma Thompson', Created_Date: '2023-11-12' }
  ]
};

export const DataImport: React.FC = () => {
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [selectedTable, setSelectedTable] = useState<DataTable | null>(null);
  const [tableData, setTableData] = useState<TableData[]>([]);
  const [isLoadingTables, setIsLoadingTables] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [searchTerm, setSearchTerm] = useState('');

  const handleSourceSelect = useCallback(async (source: DataSource) => {
    setSelectedSource(source);
    setSelectedTable(null);
    setTableData([]);
    setIsLoadingTables(true);
    
    // Simulate API call to fetch tables
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoadingTables(false);
  }, []);

  const handleTableSelect = useCallback(async (table: DataTable) => {
    setSelectedTable(table);
    setIsLoadingData(true);
    
    // Simulate API call to fetch table data
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const tableKey = `${selectedSource?.id}-${table.name}`;
    const data = mockTableData[tableKey] || [];
    setTableData(data);
    setIsLoadingData(false);
  }, [selectedSource]);

  const handleImportData = useCallback(async () => {
    if (!selectedSource || !selectedTable) return;
    
    setIsImporting(true);
    setImportStatus('idle');
    
    try {
      // Simulate import process
      await new Promise(resolve => setTimeout(resolve, 3000));
      setImportStatus('success');
    } catch (error) {
      setImportStatus('error');
    } finally {
      setIsImporting(false);
    }
  }, [selectedSource, selectedTable]);

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

  const availableTables = selectedSource ? mockTables[selectedSource.id] || [] : [];

  return (
    <div className="p-6 space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Import</h2>
        <p className="text-gray-600">Import data from connected systems into the knowledge graph</p>
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
              <button className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100">
                <RefreshCw className="w-4 h-4" />
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
            {filteredSources.map((source) => (
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
            
            {selectedSource && !isLoadingTables && availableTables.map((table) => (
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
                  <span className="text-sm text-gray-500">{table.recordCount.toLocaleString()} records</span>
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