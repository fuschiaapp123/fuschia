import React, { useState } from 'react';
import { BarChart3, Clock, Activity, TrendingUp, AlertTriangle, Users, Filter, Download } from 'lucide-react';

export const ProcessAnalysis: React.FC = () => {
  const [selectedProcess, setSelectedProcess] = useState('order-to-cash');
  const [timeRange, setTimeRange] = useState('last-30-days');

  return (
    <div className="p-6 space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Process Analysis</h2>
          <p className="text-gray-600 mt-1">
            Analyze process performance, bottlenecks, and optimization opportunities
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select 
            value={selectedProcess}
            onChange={(e) => setSelectedProcess(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="order-to-cash">Order-to-Cash</option>
            <option value="procure-to-pay">Procure-to-Pay</option>
            <option value="incident-management">Incident Management</option>
            <option value="customer-onboarding">Customer Onboarding</option>
          </select>
          
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="last-7-days">Last 7 days</option>
            <option value="last-30-days">Last 30 days</option>
            <option value="last-90-days">Last 90 days</option>
            <option value="last-year">Last year</option>
          </select>
          
          <button className="flex items-center space-x-2 px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Cases</p>
              <p className="text-2xl font-bold text-gray-900">12,543</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 8.2% vs previous period</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg. Throughput Time</p>
              <p className="text-2xl font-bold text-gray-900">4.2 days</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-sm text-red-600 mt-2">↑ 12% slower than target</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Process Variants</p>
              <p className="text-2xl font-bold text-gray-900">47</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-2">23 are main variants</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bottleneck Score</p>
              <p className="text-2xl font-bold text-gray-900">6.8</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm text-red-600 mt-2">High bottleneck activity</p>
        </div>
      </div>

      {/* Process Performance Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Throughput Time Trend</h3>
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-2" />
            <p>Chart visualization would be rendered here</p>
            <p className="text-sm">Showing throughput time over selected period</p>
          </div>
        </div>
      </div>

      {/* Bottleneck Analysis */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Bottleneck Analysis</h3>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                activity: "Credit Check",
                avgWaitTime: "2.1 days",
                frequency: "98%",
                impact: "High",
                recommendation: "Automate approval for low-risk customers"
              },
              {
                activity: "Inventory Allocation",
                avgWaitTime: "1.8 days", 
                frequency: "87%",
                impact: "Medium",
                recommendation: "Implement real-time inventory tracking"
              },
              {
                activity: "Customer Approval",
                avgWaitTime: "3.2 days",
                frequency: "34%",
                impact: "High",
                recommendation: "Send automated reminders to customers"
              },
              {
                activity: "Quality Control",
                avgWaitTime: "0.8 days",
                frequency: "76%",
                impact: "Low",
                recommendation: "Optimize batch processing schedule"
              }
            ].map((bottleneck, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    bottleneck.impact === 'High' 
                      ? 'bg-red-100' 
                      : bottleneck.impact === 'Medium' 
                      ? 'bg-orange-100' 
                      : 'bg-yellow-100'
                  }`}>
                    <AlertTriangle className={`w-5 h-5 ${
                      bottleneck.impact === 'High' 
                        ? 'text-red-600' 
                        : bottleneck.impact === 'Medium' 
                        ? 'text-orange-600' 
                        : 'text-yellow-600'
                    }`} />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{bottleneck.activity}</h4>
                    <p className="text-sm text-gray-600">{bottleneck.recommendation}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{bottleneck.avgWaitTime}</p>
                    <p className="text-xs text-gray-500">Avg Wait Time</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{bottleneck.frequency}</p>
                    <p className="text-xs text-gray-500">Frequency</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      bottleneck.impact === 'High' 
                        ? 'bg-red-100 text-red-800'
                        : bottleneck.impact === 'Medium'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {bottleneck.impact}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Process Variants */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Most Frequent Process Variants</h3>
            <button className="flex items-center space-x-2 text-sm text-indigo-600 hover:text-indigo-700">
              <Filter className="w-4 h-4" />
              <span>Filter Variants</span>
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                variant: "Standard Path",
                frequency: "34.2%",
                avgDuration: "3.1 days",
                activities: ["Order Entry", "Credit Check", "Inventory", "Shipping", "Invoice"],
                cases: 4287
              },
              {
                variant: "Express Path", 
                frequency: "28.6%",
                avgDuration: "1.8 days",
                activities: ["Order Entry", "Inventory", "Shipping", "Invoice"],
                cases: 3589
              },
              {
                variant: "Manual Review Path",
                frequency: "18.9%",
                avgDuration: "6.4 days", 
                activities: ["Order Entry", "Credit Check", "Manual Review", "Approval", "Inventory", "Shipping", "Invoice"],
                cases: 2371
              },
              {
                variant: "Return Path",
                frequency: "12.1%",
                avgDuration: "4.7 days",
                activities: ["Order Entry", "Credit Check", "Inventory", "Shipping", "Return", "Refund"],
                cases: 1518
              }
            ].map((variant, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <h4 className="font-medium text-gray-900">{variant.variant}</h4>
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {variant.frequency}
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>{variant.cases} cases</span>
                    <span>Avg: {variant.avgDuration}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {variant.activities.map((activity, actIndex) => (
                    <React.Fragment key={actIndex}>
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {activity}
                      </span>
                      {actIndex < variant.activities.length - 1 && (
                        <span className="text-gray-400">→</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};