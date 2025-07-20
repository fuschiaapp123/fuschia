import React from 'react';
import { Search, Activity, Target, Clock, Database, TrendingUp, AlertCircle, CheckCircle, Users, BarChart3 } from 'lucide-react';

export const ProcessMiningOverview: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Process Mining Platform</h2>
            <p className="text-indigo-100 max-w-2xl">
              Automatically discover, monitor, and improve your business processes using 
              event log data from your systems. Gain insights into process execution and identify optimization opportunities.
            </p>
          </div>
          <Search className="w-16 h-16 text-indigo-200" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Processes Analyzed</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 6 new this month</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg. Process Time</p>
              <p className="text-2xl font-bold text-gray-900">4.2 days</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↓ 18% improvement</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Event Logs</p>
              <p className="text-2xl font-bold text-gray-900">2.4M</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-2">Events processed</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Conformance Rate</p>
              <p className="text-2xl font-bold text-gray-900">89%</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 5% vs baseline</p>
        </div>
      </div>

      {/* Recent Process Discoveries */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Recent Process Discoveries</h3>
            <button className="text-sm text-indigo-600 hover:text-indigo-700">View All</button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                name: "Order-to-Cash Process",
                status: "Active",
                variants: 23,
                avgDuration: "5.2 days",
                conformance: "92%",
                lastUpdated: "2 hours ago",
                issues: 3
              },
              {
                name: "Procurement Process",
                status: "In Analysis",
                variants: 45,
                avgDuration: "12.8 days",
                conformance: "78%",
                lastUpdated: "1 day ago",
                issues: 8
              },
              {
                name: "Invoice Processing",
                status: "Optimized",
                variants: 12,
                avgDuration: "2.1 days",
                conformance: "96%",
                lastUpdated: "3 hours ago",
                issues: 1
              },
              {
                name: "Customer Support",
                status: "Active",
                variants: 67,
                avgDuration: "18 hours",
                conformance: "85%",
                lastUpdated: "5 hours ago",
                issues: 5
              }
            ].map((process, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Activity className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{process.name}</h4>
                    <p className="text-sm text-gray-600">Updated {process.lastUpdated}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{process.variants}</p>
                    <p className="text-xs text-gray-500">Variants</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{process.avgDuration}</p>
                    <p className="text-xs text-gray-500">Avg Duration</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{process.conformance}</p>
                    <p className="text-xs text-gray-500">Conformance</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-1">
                      <AlertCircle className="w-4 h-4 text-orange-500" />
                      <span className="text-sm font-medium text-gray-900">{process.issues}</span>
                    </div>
                    <p className="text-xs text-gray-500">Issues</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      process.status === 'Active' 
                        ? 'bg-green-100 text-green-800'
                        : process.status === 'In Analysis'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {process.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Search className="w-5 h-5 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Discover Process</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Upload event logs to automatically discover process models
          </p>
          <button className="w-full py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 transition-colors">
            Start Discovery
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Analyze Performance</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Deep dive into process performance metrics and bottlenecks
          </p>
          <button className="w-full py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors">
            View Analysis
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Check Conformance</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Compare actual process execution with reference models
          </p>
          <button className="w-full py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors">
            Run Check
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-orange-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Optimization</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Get AI-powered recommendations for process improvements
          </p>
          <button className="w-full py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors">
            Get Insights
          </button>
        </div>
      </div>

      {/* Data Sources */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Connected Data Sources</h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { name: "ServiceNow", type: "ITSM", events: "1.2M", status: "Connected" },
              { name: "SAP ERP", type: "ERP", events: "856K", status: "Connected" },
              { name: "Salesforce", type: "CRM", events: "423K", status: "Connected" },
              { name: "Workday", type: "HCM", events: "234K", status: "Pending" },
              { name: "Oracle DB", type: "Database", events: "1.8M", status: "Connected" },
              { name: "Custom API", type: "API", events: "67K", status: "Error" }
            ].map((source, index) => (
              <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Database className="w-4 h-4 text-gray-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{source.name}</h4>
                    <p className="text-xs text-gray-500">{source.type} • {source.events} events</p>
                  </div>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                  source.status === 'Connected' 
                    ? 'bg-green-100 text-green-800'
                    : source.status === 'Pending'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {source.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};