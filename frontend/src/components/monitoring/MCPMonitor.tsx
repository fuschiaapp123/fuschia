import React, { useState, useEffect } from 'react';
import { cn } from '@/utils/cn';
import {
  Server,
  Play,
  Pause,
  Settings,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  TestTube,
  Zap,
  Mail,
  Briefcase
} from 'lucide-react';
import { api } from '@/utils/api';

interface MCPService {
  service_id: string;
  service_name: string;
  is_running: boolean;
  status: string;
  capabilities: string[];
  config: {
    enabled: boolean;
    auto_start: boolean;
  };
  error?: string;
}

const SERVICE_ICONS: Record<string, React.ReactNode> = {
  gmail: <Mail className="w-6 h-6" />,
  hcmpro: <Briefcase className="w-6 h-6" />,
  default: <Server className="w-6 h-6" />
};

const SERVICE_COLORS: Record<string, string> = {
  gmail: 'blue',
  hcmpro: 'purple',
  default: 'gray'
};

export const MCPMonitor: React.FC = () => {
  const [services, setServices] = useState<MCPService[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedService, setSelectedService] = useState<string | null>(null);

  useEffect(() => {
    fetchServices();
    // Poll for status updates every 10 seconds
    const interval = setInterval(fetchServices, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchServices = async () => {
    try {
      const response = await api.get('/mcp-monitor/services');
      setServices(response.data);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch MCP services:', error);
      setError('Failed to fetch MCP services');
    }
  };

  const startService = async (serviceId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post(`/mcp-monitor/services/${serviceId}/start`);
      await fetchServices();
    } catch (error: any) {
      setError(error.response?.data?.detail || `Failed to start ${serviceId} service`);
    } finally {
      setIsLoading(false);
    }
  };

  const stopService = async (serviceId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.post(`/mcp-monitor/services/${serviceId}/stop`);
      await fetchServices();
    } catch (error: any) {
      setError(error.response?.data?.detail || `Failed to stop ${serviceId} service`);
    } finally {
      setIsLoading(false);
    }
  };

  const testConnection = async (serviceId: string) => {
    setIsLoading(true);
    try {
      const response = await api.post(`/mcp-monitor/services/${serviceId}/test`);
      if (response.data.success) {
        alert(`✅ ${serviceId} connection test successful`);
      } else {
        alert(`❌ ${serviceId} connection test failed: ${response.data.message}`);
      }
    } catch (error: any) {
      alert(`❌ Connection test failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getServiceIcon = (serviceId: string) => {
    return SERVICE_ICONS[serviceId] || SERVICE_ICONS.default;
  };

  const getServiceColor = (serviceId: string) => {
    return SERVICE_COLORS[serviceId] || SERVICE_COLORS.default;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'stopped':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Server className="w-6 h-6 text-fuschia-600" />
          <h2 className="text-2xl font-bold text-gray-900">MCP Services Monitor</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchServices}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {services.map((service) => {
          const color = getServiceColor(service.service_id);
          return (
            <div
              key={service.service_id}
              className={cn(
                "bg-white border-2 rounded-lg p-6 transition-all",
                selectedService === service.service_id ? `border-${color}-300 shadow-lg` : "border-gray-200"
              )}
              onClick={() => setSelectedService(service.service_id)}
            >
              {/* Service Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 bg-${color}-100 rounded-lg text-${color}-600`}>
                    {getServiceIcon(service.service_id)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{service.service_name}</h3>
                    <p className="text-xs text-gray-500">{service.service_id}</p>
                  </div>
                </div>
                <div className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-full",
                  service.is_running ? "bg-green-100" : "bg-gray-100"
                )}>
                  {service.is_running ? (
                    <Zap className="w-5 h-5 text-green-600" />
                  ) : (
                    <Pause className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Status Badge */}
              <div className="mb-4">
                <span className={cn(
                  "px-3 py-1 text-xs font-medium rounded-full",
                  getStatusBadge(service.status)
                )}>
                  {service.status.toUpperCase()}
                </span>
                {service.error && (
                  <p className="text-xs text-red-600 mt-2">{service.error}</p>
                )}
              </div>

              {/* Capabilities */}
              <div className="mb-4">
                <p className="text-xs font-medium text-gray-700 mb-2">Capabilities:</p>
                <div className="flex flex-wrap gap-1">
                  {service.capabilities.map((capability, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      {capability.replace(`${service.service_id}_`, '')}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2">
                {service.is_running ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      stopService(service.service_id);
                    }}
                    disabled={isLoading}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50 text-sm"
                  >
                    <Pause className="w-4 h-4" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startService(service.service_id);
                    }}
                    disabled={isLoading}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 text-sm"
                  >
                    <Play className="w-4 h-4" />
                    <span>Start</span>
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    testConnection(service.service_id);
                  }}
                  disabled={isLoading || !service.is_running}
                  className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                >
                  <TestTube className="w-4 h-4" />
                </button>
              </div>

              {/* Configuration */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className={cn(
                      "w-3 h-3",
                      service.config.enabled ? "text-green-500" : "text-gray-300"
                    )} />
                    <span className="text-gray-600">Enabled</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Zap className={cn(
                      "w-3 h-3",
                      service.config.auto_start ? "text-blue-500" : "text-gray-300"
                    )} />
                    <span className="text-gray-600">Auto-start</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {services.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <Server className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No MCP services configured</p>
        </div>
      )}

      {/* Service Details Panel */}
      {selectedService && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Service Details</h3>
            <button
              onClick={() => setSelectedService(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          {(() => {
            const service = services.find(s => s.service_id === selectedService);
            if (!service) return null;

            return (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Service ID</p>
                    <p className="text-sm text-gray-900">{service.service_id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">Service Name</p>
                    <p className="text-sm text-gray-900">{service.service_name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">Status</p>
                    <span className={cn(
                      "inline-block px-2 py-1 text-xs font-medium rounded",
                      getStatusBadge(service.status)
                    )}>
                      {service.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">Running</p>
                    <p className="text-sm text-gray-900">{service.is_running ? 'Yes' : 'No'}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Capabilities</p>
                  <div className="bg-gray-50 rounded-md p-3">
                    <ul className="list-disc list-inside space-y-1">
                      {service.capabilities.map((capability, index) => (
                        <li key={index} className="text-sm text-gray-700">{capability}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {service.error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-sm font-medium text-red-800">Error</p>
                    <p className="text-sm text-red-700 mt-1">{service.error}</p>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};
