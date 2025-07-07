import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  Play, 
  Trash2, 
  Download, 
  Settings, 
  Database,
  Maximize2,
  Search,
  FileText,
  BarChart3,
  RefreshCw,
  Info,
  Bookmark,
  Clock
} from 'lucide-react';

import { Neo4jVisualization } from './Neo4jVisualization';

interface Neo4jNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

interface Neo4jRelationship {
  id: string;
  type: string;
  startNodeId: string;
  endNodeId: string;
  properties: Record<string, any>;
}

interface QueryResult {
  nodes: Neo4jNode[];
  relationships: Neo4jRelationship[];
  summary: {
    resultAvailableAfter: number;
    resultConsumedAfter: number;
    counters: {
      nodesCreated: number;
      relationshipsCreated: number;
      propertiesSet: number;
    };
  };
}

interface QueryHistory {
  id: string;
  query: string;
  timestamp: Date;
  executionTime: number;
  success: boolean;
  resultCount: number;
}

export const Neo4jBrowser: React.FC = () => {
  const [query, setQuery] = useState('MATCH (n) RETURN n LIMIT 25');
  const [isExecuting, setIsExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);
  const [selectedTab, setSelectedTab] = useState<'graph' | 'table' | 'text'>('graph');
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [selectedNode, setSelectedNode] = useState<Neo4jNode | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<Neo4jRelationship | null>(null);

  // Sample data
  const sampleNodes: Neo4jNode[] = [
    {
      id: '1',
      labels: ['Department'],
      properties: { name: 'Customer Service', employees: 25, location: 'Building A' }
    },
    {
      id: '2',
      labels: ['System'],
      properties: { name: 'ServiceNow', type: 'ITSM', version: 'Paris' }
    },
    {
      id: '3',
      labels: ['System'],
      properties: { name: 'Salesforce', type: 'CRM', edition: 'Enterprise' }
    },
    {
      id: '4',
      labels: ['Process'],
      properties: { name: 'Incident Management', sla: '4 hours', priority_levels: 4 }
    },
    {
      id: '5',
      labels: ['Person'],
      properties: { name: 'John Smith', role: 'IT Manager', department: 'IT' }
    },
    {
      id: '6',
      labels: ['Entity'],
      properties: { name: 'Customer Account', total: 1245, active: 1156 }
    }
  ];

  const sampleRelationships: Neo4jRelationship[] = [
    {
      id: 'r1',
      type: 'USES',
      startNodeId: '1',
      endNodeId: '2',
      properties: { since: '2020-01-01' }
    },
    {
      id: 'r2',
      type: 'USES',
      startNodeId: '1',
      endNodeId: '3',
      properties: { since: '2019-06-15' }
    },
    {
      id: 'r3',
      type: 'SUPPORTS',
      startNodeId: '2',
      endNodeId: '4',
      properties: { criticality: 'high' }
    },
    {
      id: 'r4',
      type: 'ASSIGNED_TO',
      startNodeId: '4',
      endNodeId: '5',
      properties: { role: 'owner' }
    },
    {
      id: 'r5',
      type: 'MANAGES',
      startNodeId: '3',
      endNodeId: '6',
      properties: { access_level: 'full' }
    }
  ];

  // Initialize with sample data
  useEffect(() => {
    // Set initial result
    setQueryResult({
      nodes: sampleNodes,
      relationships: sampleRelationships,
      summary: {
        resultAvailableAfter: 45,
        resultConsumedAfter: 12,
        counters: {
          nodesCreated: 0,
          relationshipsCreated: 0,
          propertiesSet: 0
        }
      }
    });
  }, []);

  const handleNodeClick = useCallback((node: Neo4jNode) => {
    setSelectedNode(node);
    console.log('Node clicked:', node);
  }, []);

  const handleRelationshipClick = useCallback((relationship: Neo4jRelationship) => {
    setSelectedRelationship(relationship);
    console.log('Relationship clicked:', relationship);
  }, []);

  const executeQuery = useCallback(async () => {
    if (!query.trim()) return;

    setIsExecuting(true);
    const startTime = Date.now();

    try {
      // Simulate query execution
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock different query results based on query content
      let resultNodes = sampleNodes;
      let resultRelationships = sampleRelationships;

      if (query.toLowerCase().includes('person')) {
        resultNodes = sampleNodes.filter(n => n.labels.includes('Person'));
        resultRelationships = sampleRelationships.filter(r => 
          resultNodes.some(n => n.id === r.startNodeId) || 
          resultNodes.some(n => n.id === r.endNodeId)
        );
      } else if (query.toLowerCase().includes('system')) {
        resultNodes = sampleNodes.filter(n => n.labels.includes('System'));
        resultRelationships = sampleRelationships.filter(r => 
          resultNodes.some(n => n.id === r.startNodeId) || 
          resultNodes.some(n => n.id === r.endNodeId)
        );
      }

      const executionTime = Date.now() - startTime;

      // Set result
      setQueryResult({
        nodes: resultNodes,
        relationships: resultRelationships,
        summary: {
          resultAvailableAfter: executionTime - 100,
          resultConsumedAfter: 100,
          counters: {
            nodesCreated: 0,
            relationshipsCreated: 0,
            propertiesSet: 0
          }
        }
      });

      // Add to history
      setQueryHistory(prev => [{
        id: Date.now().toString(),
        query,
        timestamp: new Date(),
        executionTime,
        success: true,
        resultCount: resultNodes.length + resultRelationships.length
      }, ...prev.slice(0, 9)]);

    } catch (error) {
      console.error('Query execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  }, [query]);

  const quickQueries = [
    'MATCH (n) RETURN n LIMIT 25',
    'MATCH (p:Person) RETURN p',
    'MATCH (s:System) RETURN s',
    'MATCH (d:Department)-[r]-(s:System) RETURN d,r,s',
    'MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50'
  ];

  return (
    <div className="h-full flex bg-gray-50">
      {/* Sidebar */}
      {sidebarVisible && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-2 mb-4">
              <Database className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Knowledge Graph</h3>
            </div>
            
            {/* Quick Queries */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Queries</h4>
              {quickQueries.map((q, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(q)}
                  className="w-full text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border font-mono"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Query History */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              Query History
            </h4>
            <div className="space-y-2">
              {queryHistory.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setQuery(item.query)}
                  className="p-3 bg-gray-50 hover:bg-gray-100 rounded border cursor-pointer"
                >
                  <div className="text-xs font-mono text-gray-900 mb-1 truncate">
                    {item.query}
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{item.timestamp.toLocaleTimeString()}</span>
                    <span>{item.executionTime}ms</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.resultCount} results
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              Connected to Knowledge Graph
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            >
              <Database className="w-4 h-4" />
            </button>
            
            <div className="flex-1 flex items-center space-x-2">
              <div className="flex-1 relative">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                      executeQuery();
                    }
                  }}
                  placeholder="Enter Cypher query..."
                  className="w-full p-3 border border-gray-300 rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={2}
                />
              </div>
              
              <button
                onClick={executeQuery}
                disabled={isExecuting}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isExecuting ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span>Run</span>
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
                <Bookmark className="w-4 h-4" />
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
                <Download className="w-4 h-4" />
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Result Tabs */}
        <div className="bg-white border-b border-gray-200">
          <div className="flex items-center space-x-4 px-4">
            <button
              onClick={() => setSelectedTab('graph')}
              className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                selectedTab === 'graph'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Graph</span>
            </button>
            
            <button
              onClick={() => setSelectedTab('table')}
              className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                selectedTab === 'table'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Table</span>
            </button>
            
            <button
              onClick={() => setSelectedTab('text')}
              className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                selectedTab === 'text'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Info className="w-4 h-4" />
              <span>Text</span>
            </button>

            {queryResult && (
              <div className="ml-auto text-sm text-gray-500">
                {queryResult.nodes.length} nodes, {queryResult.relationships.length} relationships
                {queryResult.summary.resultAvailableAfter && (
                  <span className="ml-2">
                    ({queryResult.summary.resultAvailableAfter + queryResult.summary.resultConsumedAfter}ms)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {selectedTab === 'graph' && queryResult && (
            <div className="h-full p-4">
              <div className="w-full h-full bg-white rounded-lg border border-gray-200">
                <Neo4jVisualization
                  nodes={queryResult.nodes}
                  relationships={queryResult.relationships}
                  onNodeClick={handleNodeClick}
                  onRelationshipClick={handleRelationshipClick}
                  config={{
                    layout: 'force-directed',
                    physics: true,
                    nodeStyle: {
                      'Person': { color: '#ec4899' },
                      'System': { color: '#8b5cf6' },
                      'Department': { color: '#3b82f6' },
                      'Process': { color: '#10b981' },
                      'Entity': { color: '#f59e0b' }
                    }
                  }}
                />
              </div>
            </div>
          )}

          {selectedTab === 'table' && queryResult && (
            <div className="h-full overflow-auto p-4">
              <div className="bg-white rounded-lg border border-gray-200">
                {/* Nodes Table */}
                {queryResult.nodes.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 p-4 border-b border-gray-200">
                      Nodes ({queryResult.nodes.length})
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Labels</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Properties</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {queryResult.nodes.map((node) => (
                            <tr key={node.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-900">{node.id}</td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                {node.labels.map(label => (
                                  <span key={label} className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded mr-1">
                                    {label}
                                  </span>
                                ))}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                <pre className="text-xs">{JSON.stringify(node.properties, null, 2)}</pre>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Relationships Table */}
                {queryResult.relationships.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 p-4 border-b border-gray-200">
                      Relationships ({queryResult.relationships.length})
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Start Node</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">End Node</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Properties</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {queryResult.relationships.map((rel) => (
                            <tr key={rel.id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-900">{rel.id}</td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                                  {rel.type}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">{rel.startNodeId}</td>
                              <td className="px-4 py-3 text-sm text-gray-900">{rel.endNodeId}</td>
                              <td className="px-4 py-3 text-sm text-gray-900">
                                <pre className="text-xs">{JSON.stringify(rel.properties, null, 2)}</pre>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedTab === 'text' && queryResult && (
            <div className="h-full overflow-auto p-4">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Result Summary</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900">Execution Summary</h4>
                    <p className="text-sm text-gray-600">
                      Query returned {queryResult.nodes.length} nodes and {queryResult.relationships.length} relationships
                    </p>
                    <p className="text-sm text-gray-600">
                      Execution time: {queryResult.summary.resultAvailableAfter + queryResult.summary.resultConsumedAfter}ms
                    </p>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">Node Labels</h4>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Array.from(new Set(queryResult.nodes.flatMap(n => n.labels))).map(label => (
                        <span key={label} className="inline-block px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded">
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900">Relationship Types</h4>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {Array.from(new Set(queryResult.relationships.map(r => r.type))).map(type => (
                        <span key={type} className="inline-block px-3 py-1 text-sm bg-green-100 text-green-800 rounded">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};