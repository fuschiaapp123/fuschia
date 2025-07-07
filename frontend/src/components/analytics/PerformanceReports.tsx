import React, { useState } from 'react';
import { 
  Download, 
  Calendar, 
  FileText, 
  TrendingUp, 
  BarChart3,
  PieChart,
  Activity,
  Filter,
  RefreshCw
} from 'lucide-react';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: 'workflow' | 'agent' | 'system' | 'summary';
  lastGenerated: string;
  format: 'PDF' | 'CSV' | 'Excel';
}

const reportTemplates: ReportTemplate[] = [
  {
    id: '1',
    name: 'Weekly Workflow Summary',
    description: 'Comprehensive overview of workflow performance and metrics',
    category: 'workflow',
    lastGenerated: '2 hours ago',
    format: 'PDF'
  },
  {
    id: '2',
    name: 'Agent Performance Report',
    description: 'Detailed analysis of individual agent metrics and utilization',
    category: 'agent',
    lastGenerated: '1 day ago',
    format: 'Excel'
  },
  {
    id: '3',
    name: 'System Health Dashboard',
    description: 'Infrastructure metrics, uptime, and resource utilization',
    category: 'system',
    lastGenerated: '6 hours ago',
    format: 'PDF'
  },
  {
    id: '4',
    name: 'Monthly Executive Summary',
    description: 'High-level KPIs and business impact metrics',
    category: 'summary',
    lastGenerated: '3 days ago',
    format: 'PDF'
  },
  {
    id: '5',
    name: 'Error Analysis Report',
    description: 'Failed executions, error patterns, and resolution trends',
    category: 'workflow',
    lastGenerated: '12 hours ago',
    format: 'CSV'
  },
  {
    id: '6',
    name: 'Agent Workload Distribution',
    description: 'Task distribution and load balancing across agent network',
    category: 'agent',
    lastGenerated: '4 hours ago',
    format: 'Excel'
  }
];

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'workflow':
      return 'bg-blue-100 text-blue-800';
    case 'agent':
      return 'bg-green-100 text-green-800';
    case 'system':
      return 'bg-purple-100 text-purple-800';
    case 'summary':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'workflow':
      return <BarChart3 className="w-4 h-4" />;
    case 'agent':
      return <Activity className="w-4 h-4" />;
    case 'system':
      return <PieChart className="w-4 h-4" />;
    case 'summary':
      return <TrendingUp className="w-4 h-4" />;
    default:
      return <FileText className="w-4 h-4" />;
  }
};

export const PerformanceReports: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFormat, setSelectedFormat] = useState('all');
  const [isGenerating, setIsGenerating] = useState<string | null>(null);

  const filteredReports = reportTemplates.filter(report => {
    const categoryMatch = selectedCategory === 'all' || report.category === selectedCategory;
    const formatMatch = selectedFormat === 'all' || report.format === selectedFormat;
    return categoryMatch && formatMatch;
  });

  const handleGenerateReport = async (reportId: string) => {
    setIsGenerating(reportId);
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsGenerating(null);
    
    // Simulate download
    const report = reportTemplates.find(r => r.id === reportId);
    if (report) {
      const blob = new Blob([`${report.name} - Generated on ${new Date().toLocaleString()}`], {
        type: 'text/plain',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.name.replace(/\s+/g, '_')}.${report.format.toLowerCase()}`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const kpiData = [
    { label: 'Reports Generated', value: 247, change: '+12%' },
    { label: 'Scheduled Reports', value: 18, change: '+3' },
    { label: 'Data Sources', value: 8, change: '0' },
    { label: 'Average Generation Time', value: '2.3s', change: '-15%' }
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Performance Reports</h2>
          <p className="text-gray-600">Generate and download comprehensive analytics reports</p>
        </div>
        
        <button className="flex items-center space-x-2 px-4 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 transition-colors">
          <Calendar className="w-4 h-4" />
          <span>Schedule Report</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi, index) => (
          <div key={index} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{kpi.label}</p>
                <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
              </div>
              <div className="p-3 bg-fuschia-100 rounded-lg">
                <FileText className="w-6 h-6 text-fuschia-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-600">{kpi.change} from last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filters:</span>
          </div>
          
          <select 
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
          >
            <option value="all">All Categories</option>
            <option value="workflow">Workflow Reports</option>
            <option value="agent">Agent Reports</option>
            <option value="system">System Reports</option>
            <option value="summary">Summary Reports</option>
          </select>
          
          <select 
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-fuschia-500"
          >
            <option value="all">All Formats</option>
            <option value="PDF">PDF</option>
            <option value="Excel">Excel</option>
            <option value="CSV">CSV</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">{filteredReports.length} reports available</span>
          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Report Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredReports.map((report) => (
          <div key={report.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  {getCategoryIcon(report.category)}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{report.name}</h3>
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(report.category)}`}>
                    {report.category}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">{report.format}</div>
                <div className="text-xs text-gray-500">Format</div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              {report.description}
            </p>
            
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs text-gray-500">
                Last generated: {report.lastGenerated}
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={() => handleGenerateReport(report.id)}
                disabled={isGenerating === report.id}
                className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                {isGenerating === report.id ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Generate</span>
                  </>
                )}
              </button>
              
              <button className="flex items-center justify-center px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
                <Calendar className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Reports Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Report Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Format
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Generated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reportTemplates.slice(0, 5).map((report, index) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8">
                        <div className="h-8 w-8 rounded-full bg-fuschia-100 flex items-center justify-center">
                          {getCategoryIcon(report.category)}
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{report.name}</div>
                        <div className="text-sm text-gray-500">{report.description.substring(0, 50)}...</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(report.category)}`}>
                      {report.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {report.format}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.lastGenerated}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(Math.random() * 5 + 0.5).toFixed(1)} MB
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-fuschia-600 hover:text-fuschia-900 mr-4">
                      Download
                    </button>
                    <button className="text-gray-600 hover:text-gray-900">
                      Schedule
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};