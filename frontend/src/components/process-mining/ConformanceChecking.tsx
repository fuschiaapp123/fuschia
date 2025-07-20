import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Target, Upload, Play, Download, BarChart3 } from 'lucide-react';

export const ConformanceChecking: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('reference-model-1');
  const [checkingStatus, setCheckingStatus] = useState<'idle' | 'running' | 'completed'>('idle');

  const startConformanceCheck = () => {
    setCheckingStatus('running');
    setTimeout(() => setCheckingStatus('completed'), 4000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Conformance Checking</h2>
          <p className="text-gray-600 mt-1">
            Compare actual process execution with reference models to identify deviations
          </p>
        </div>
      </div>

      {/* Conformance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overall Conformance</p>
              <p className="text-2xl font-bold text-gray-900">87.3%</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 3.2% vs last check</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Conforming Cases</p>
              <p className="text-2xl font-bold text-gray-900">10,952</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-2">Out of 12,543 total</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Minor Deviations</p>
              <p className="text-2xl font-bold text-gray-900">1,234</p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <p className="text-sm text-yellow-600 mt-2">9.8% of total cases</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Major Deviations</p>
              <p className="text-2xl font-bold text-gray-900">357</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm text-red-600 mt-2">2.8% of total cases</p>
        </div>
      </div>

      {/* Model Selection and Check */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Conformance Check Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Model
            </label>
            <select 
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="reference-model-1">Order-to-Cash Reference Model v2.1</option>
              <option value="reference-model-2">Procure-to-Pay Standard Model v1.3</option>
              <option value="reference-model-3">Incident Management ITIL v4.0</option>
              <option value="custom-model">Upload Custom Model</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Event Log Period
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Last 6 months</option>
              <option>Last year</option>
              <option>Custom date range</option>
            </select>
          </div>
        </div>
        
        <div className="mt-6 flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">Run Conformance Check</h4>
            <p className="text-sm text-gray-600">Compare current process execution against reference model</p>
          </div>
          
          <div className="flex items-center space-x-3">
            {checkingStatus === 'idle' && (
              <button
                onClick={startConformanceCheck}
                className="flex items-center space-x-2 px-6 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
              >
                <Play className="w-4 h-4" />
                <span>Start Check</span>
              </button>
            )}
            
            {checkingStatus === 'running' && (
              <div className="flex items-center space-x-2 text-indigo-600">
                <div className="animate-spin w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
                <span>Analyzing conformance...</span>
              </div>
            )}
            
            {checkingStatus === 'completed' && (
              <div className="flex items-center space-x-3">
                <span className="text-green-600">✅ Check completed</span>
                <button className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600">
                  <Download className="w-4 h-4" />
                  <span>Download Report</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Conformance Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Deviation Types */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Deviation Types</h3>
          </div>
          
          <div className="p-6">
            <div className="space-y-4">
              {[
                {
                  type: "Skip Activity",
                  description: "Required activities were skipped",
                  count: 892,
                  severity: "medium",
                  examples: ["Credit Check skipped in 534 cases", "Quality Control skipped in 358 cases"]
                },
                {
                  type: "Wrong Order",
                  description: "Activities executed in wrong sequence",
                  count: 456,
                  severity: "high",
                  examples: ["Invoice sent before shipping in 289 cases", "Approval after execution in 167 cases"]
                },
                {
                  type: "Extra Activity",
                  description: "Additional unexpected activities",
                  count: 234,
                  severity: "low",
                  examples: ["Additional approvals in 134 cases", "Extra quality checks in 100 cases"]
                },
                {
                  type: "Resource Violation",
                  description: "Wrong resource assignments",
                  count: 189,
                  severity: "medium",
                  examples: ["Junior staff handling senior tasks", "Cross-department violations"]
                }
              ].map((deviation, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{deviation.type}</h4>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">{deviation.count}</span>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        deviation.severity === 'high' 
                          ? 'bg-red-100 text-red-800'
                          : deviation.severity === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {deviation.severity}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{deviation.description}</p>
                  <div className="text-xs text-gray-500">
                    {deviation.examples.map((example, exIndex) => (
                      <div key={exIndex}>• {example}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Conformance by Activity */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Conformance by Activity</h3>
          </div>
          
          <div className="p-6">
            <div className="space-y-4">
              {[
                { activity: "Order Entry", conformance: 98.5, deviations: 18 },
                { activity: "Credit Check", conformance: 76.2, deviations: 534 },
                { activity: "Inventory Allocation", conformance: 91.3, deviations: 156 },
                { activity: "Customer Approval", conformance: 89.7, deviations: 234 },
                { activity: "Shipping", conformance: 94.8, deviations: 89 },
                { activity: "Invoice Generation", conformance: 87.4, deviations: 298 },
                { activity: "Payment Processing", conformance: 95.1, deviations: 67 },
                { activity: "Order Completion", conformance: 99.2, deviations: 12 }
              ].map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900">{activity.activity}</span>
                      <span className="text-sm font-medium text-gray-900">{activity.conformance}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          activity.conformance >= 95 
                            ? 'bg-green-500' 
                            : activity.conformance >= 85 
                            ? 'bg-yellow-500' 
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${activity.conformance}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {activity.deviations} deviations found
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Conformance Checks */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Conformance Checks</h3>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                model: "Order-to-Cash Reference Model v2.1",
                date: "2 hours ago",
                conformance: 87.3,
                cases: 12543,
                deviations: 1591,
                status: "Completed"
              },
              {
                model: "Procure-to-Pay Standard Model v1.3", 
                date: "1 day ago",
                conformance: 82.1,
                cases: 8934,
                deviations: 1598,
                status: "Completed"
              },
              {
                model: "Incident Management ITIL v4.0",
                date: "3 days ago",
                conformance: 91.7,
                cases: 15678,
                deviations: 1301,
                status: "Completed"
              }
            ].map((check, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{check.model}</h4>
                    <p className="text-sm text-gray-600">Checked {check.date}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{check.conformance}%</p>
                    <p className="text-xs text-gray-500">Conformance</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{check.cases.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">Cases</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{check.deviations}</p>
                    <p className="text-xs text-gray-500">Deviations</p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                      {check.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};