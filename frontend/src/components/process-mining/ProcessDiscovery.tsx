import React, { useState } from 'react';
import { Upload, Search, Settings, Play, Download, FileText, Database, AlertCircle } from 'lucide-react';

export const ProcessDiscovery: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [discoveryStatus, setDiscoveryStatus] = useState<'idle' | 'processing' | 'completed'>('idle');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const startDiscovery = () => {
    setDiscoveryStatus('processing');
    // Simulate process discovery
    setTimeout(() => setDiscoveryStatus('completed'), 3000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Process Discovery</h2>
          <p className="text-gray-600 mt-1">
            Automatically discover process models from event log data
          </p>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Log Upload</h3>
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          {!selectedFile ? (
            <div>
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <div className="space-y-2">
                <p className="text-lg font-medium text-gray-900">Upload event log file</p>
                <p className="text-gray-600">Support for CSV, XES, and MXML formats</p>
              </div>
              <div className="mt-4">
                <label className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 cursor-pointer">
                  <Upload className="w-4 h-4" />
                  <span>Choose File</span>
                  <input
                    type="file"
                    accept=".csv,.xes,.mxml"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          ) : (
            <div>
              <FileText className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-gray-600">File size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              <button
                onClick={() => setSelectedFile(null)}
                className="mt-2 text-sm text-red-600 hover:text-red-700"
              >
                Remove file
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Discovery Configuration */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Discovery Settings</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mining Algorithm
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option>Alpha Miner</option>
              <option>Heuristics Miner</option>
              <option>Inductive Miner</option>
              <option>ILP Miner</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Noise Threshold
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option>0% (No filtering)</option>
              <option>5% (Light filtering)</option>
              <option>10% (Moderate filtering)</option>
              <option>20% (Heavy filtering)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Case ID Column
            </label>
            <input
              type="text"
              placeholder="case_id"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Activity Column
            </label>
            <input
              type="text"
              placeholder="activity"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timestamp Column
            </label>
            <input
              type="text"
              placeholder="timestamp"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Discovery Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Start Discovery</h3>
            <p className="text-gray-600">Process the uploaded event log to discover the process model</p>
          </div>
          
          <div className="flex items-center space-x-3">
            {discoveryStatus === 'idle' && (
              <button
                onClick={startDiscovery}
                disabled={!selectedFile}
                className="flex items-center space-x-2 px-6 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                <span>Start Discovery</span>
              </button>
            )}
            
            {discoveryStatus === 'processing' && (
              <div className="flex items-center space-x-2 text-indigo-600">
                <div className="animate-spin w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
                <span>Processing...</span>
              </div>
            )}
            
            {discoveryStatus === 'completed' && (
              <div className="flex items-center space-x-3">
                <span className="text-green-600">✅ Discovery completed</span>
                <button className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600">
                  <Download className="w-4 h-4" />
                  <span>Download Model</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Discoveries */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Discoveries</h3>
        </div>
        
        <div className="p-6">
          <div className="space-y-4">
            {[
              {
                name: "Purchase-to-Pay Process",
                algorithm: "Inductive Miner",
                activities: 24,
                variants: 156,
                fitness: 0.92,
                precision: 0.87,
                status: "Completed",
                date: "2 hours ago"
              },
              {
                name: "Customer Onboarding",
                algorithm: "Heuristics Miner", 
                activities: 18,
                variants: 89,
                fitness: 0.89,
                precision: 0.91,
                status: "Completed",
                date: "1 day ago"
              },
              {
                name: "Incident Management",
                algorithm: "Alpha Miner",
                activities: 31,
                variants: 203,
                fitness: 0.85,
                precision: 0.83,
                status: "Processing",
                date: "5 minutes ago"
              }
            ].map((discovery, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Search className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{discovery.name}</h4>
                    <p className="text-sm text-gray-600">{discovery.algorithm} • {discovery.date}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{discovery.activities}</p>
                    <p className="text-xs text-gray-500">Activities</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{discovery.variants}</p>
                    <p className="text-xs text-gray-500">Variants</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{discovery.fitness}</p>
                    <p className="text-xs text-gray-500">Fitness</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      discovery.status === 'Completed' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {discovery.status}
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