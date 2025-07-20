import React from 'react';
import { TrendingUp, Clock, Users, Target, BarChart3, Plus } from 'lucide-react';

export const ValueStreamOverview: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Value Stream Management</h2>
            <p className="text-blue-100 max-w-2xl">
              Visualize, analyze, and optimize your value streams to eliminate waste, 
              reduce lead times, and improve customer value delivery.
            </p>
          </div>
          <TrendingUp className="w-16 h-16 text-blue-200" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Value Streams</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 2 new this month</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg. Lead Time</p>
              <p className="text-2xl font-bold text-gray-900">18.5 days</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↓ 15% improvement</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Teams</p>
              <p className="text-2xl font-bold text-gray-900">8</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-2">Cross-functional teams</p>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Process Efficiency</p>
              <p className="text-2xl font-bold text-gray-900">87%</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">↑ 12% vs last quarter</p>
        </div>
      </div>

      {/* Recent Value Streams */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Recent Value Streams</h3>
            <button className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
              <Plus className="w-4 h-4" />
              <span>Create New</span>
            </button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                name: "Customer Onboarding Process",
                status: "Active",
                leadTime: "12 days",
                efficiency: "92%",
                lastUpdated: "2 hours ago"
              },
              {
                name: "Product Development Lifecycle",
                status: "In Review",
                leadTime: "45 days",
                efficiency: "78%",
                lastUpdated: "1 day ago"
              },
              {
                name: "Order Fulfillment Pipeline",
                status: "Active",
                leadTime: "3 days",
                efficiency: "95%",
                lastUpdated: "3 hours ago"
              },
              {
                name: "Support Ticket Resolution",
                status: "Optimizing",
                leadTime: "8 hours",
                efficiency: "89%",
                lastUpdated: "5 hours ago"
              }
            ].map((stream, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{stream.name}</h4>
                    <p className="text-sm text-gray-600">Updated {stream.lastUpdated}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{stream.leadTime}</p>
                    <p className="text-xs text-gray-500">Lead Time</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{stream.efficiency}</p>
                    <p className="text-xs text-gray-500">Efficiency</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      stream.status === 'Active' 
                        ? 'bg-green-100 text-green-800'
                        : stream.status === 'In Review'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {stream.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Create Value Stream</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Start mapping a new value stream with our visual designer
          </p>
          <button className="w-full py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
            Get Started
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">View Analytics</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Analyze performance metrics and identify improvement opportunities
          </p>
          <button className="w-full py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors">
            View Reports
          </button>
        </div>

        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Use Templates</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Start with proven templates for common value stream patterns
          </p>
          <button className="w-full py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors">
            Browse Templates
          </button>
        </div>
      </div>
    </div>
  );
};