import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ChevronDown, ChevronRight, Settings, Trash2, Copy } from 'lucide-react';

export interface ZapierStepData {
  label: string;
  app: string;
  action: string;
  description?: string;
  stepNumber: number;
  isExpanded?: boolean;
  config?: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
}

const ZapierStepNode: React.FC<NodeProps<ZapierStepData>> = ({ data, id, selected }) => {
  const [isExpanded, setIsExpanded] = useState(data.isExpanded || false);
  const [isHovered, setIsHovered] = useState(false);

  const getAppIcon = (app: string) => {
    // In a real implementation, you'd map to actual app icons
    const iconMap: Record<string, string> = {
      'Gmail': '📧',
      'Slack': '💬',
      'Google Sheets': '📊',
      'Trello': '📋',
      'Salesforce': '☁️',
      'ServiceNow': '🎟️',
      'Webhook': '🔗',
      'Filter': '🔍',
      'Delay': '⏱️',
      'Default': '⚙️'
    };
    return iconMap[app] || iconMap['Default'];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#f59e0b';
      case 'success': return '#10b981';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleActionClick = (action: string, e: React.MouseEvent) => {
    e.stopPropagation();
    console.log(`${action} clicked for step ${id}`);
    // Implement actual actions here
  };

  return (
    <>
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: '#ff4f00',
          border: '2px solid #fff',
          width: '12px',
          height: '12px',
          top: '-6px'
        }}
      />

      <div
        className={`zapier-step-node ${selected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          background: '#fff',
          border: selected ? '2px solid #ff4f00' : '1px solid #e5e7eb',
          borderRadius: '8px',
          boxShadow: isHovered || selected ? '0 8px 25px rgba(0,0,0,0.15)' : '0 2px 8px rgba(0,0,0,0.1)',
          minWidth: '320px',
          maxWidth: '400px',
          transition: 'all 0.2s ease',
          position: 'relative'
        }}
      >
        {/* Step Number Badge */}
        <div
          style={{
            position: 'absolute',
            top: '-8px',
            left: '16px',
            background: '#ff4f00',
            color: 'white',
            borderRadius: '12px',
            width: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            fontWeight: 'bold',
            border: '2px solid #fff'
          }}
        >
          {data.stepNumber}
        </div>

        {/* Main Step Content */}
        <div style={{ padding: '20px 16px 16px 16px' }}>
          {/* Header Section */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
              {/* App Icon */}
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '6px',
                  background: '#f3f4f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '16px'
                }}
              >
                {getAppIcon(data.app)}
              </div>

              {/* App and Action */}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#1f2937' }}>
                  {data.app}
                </div>
                <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '2px' }}>
                  {data.action || 'Select an action'}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {isHovered && (
                <>
                  <button
                    onClick={(e) => handleActionClick('copy', e)}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: '4px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: '#6b7280',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title="Duplicate step"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    onClick={(e) => handleActionClick('delete', e)}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: '4px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: '#6b7280',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title="Delete step"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
              
              <button
                onClick={handleToggleExpand}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '4px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  color: '#6b7280',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            </div>
          </div>

          {/* Step Title */}
          <div style={{ fontSize: '15px', fontWeight: '500', color: '#1f2937', marginBottom: '8px' }}>
            {data.label}
          </div>

          {/* Description */}
          {data.description && (
            <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '12px' }}>
              {data.description}
            </div>
          )}

          {/* Status Indicator */}
          {data.status && data.status !== 'idle' && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 8px',
                borderRadius: '12px',
                background: `${getStatusColor(data.status)}20`,
                border: `1px solid ${getStatusColor(data.status)}40`,
                fontSize: '12px',
                fontWeight: '500',
                color: getStatusColor(data.status),
                marginBottom: '8px'
              }}
            >
              <div
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: getStatusColor(data.status)
                }}
              />
              {data.status}
            </div>
          )}

          {/* Expanded Configuration */}
          {isExpanded && (
            <div
              style={{
                marginTop: '16px',
                padding: '16px',
                background: '#f9fafb',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Settings size={16} color="#6b7280" />
                <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                  Configuration
                </span>
              </div>

              {/* App Selection */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151', display: 'block', marginBottom: '4px' }}>
                  App
                </label>
                <select
                  value={data.app}
                  onChange={(e) => {/* Handle app change */}}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    background: '#fff'
                  }}
                >
                  <option value="Gmail">📧 Gmail</option>
                  <option value="Slack">💬 Slack</option>
                  <option value="Google Sheets">📊 Google Sheets</option>
                  <option value="ServiceNow">🎟️ ServiceNow</option>
                  <option value="Webhook">🔗 Webhook</option>
                </select>
              </div>

              {/* Action Selection */}
              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151', display: 'block', marginBottom: '4px' }}>
                  Action
                </label>
                <select
                  value={data.action}
                  onChange={(e) => {/* Handle action change */}}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    background: '#fff'
                  }}
                >
                  <option value="">Select an action</option>
                  <option value="Send Email">Send Email</option>
                  <option value="Create Record">Create Record</option>
                  <option value="Update Record">Update Record</option>
                  <option value="Send Message">Send Message</option>
                </select>
              </div>

              {/* Additional Configuration Fields */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: '500', color: '#374151', display: 'block', marginBottom: '4px' }}>
                  Description
                </label>
                <textarea
                  value={data.description || ''}
                  onChange={(e) => {/* Handle description change */}}
                  placeholder="Describe what this step does..."
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '13px',
                    background: '#fff',
                    resize: 'vertical',
                    minHeight: '60px'
                  }}
                />
              </div>

              {/* Test Step Button */}
              <button
                onClick={(e) => handleActionClick('test', e)}
                style={{
                  marginTop: '12px',
                  width: '100%',
                  padding: '8px 16px',
                  background: '#ff4f00',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Test this step
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: '#ff4f00',
          border: '2px solid #fff',
          width: '12px',
          height: '12px',
          bottom: '-6px'
        }}
      />
    </>
  );
};

export default ZapierStepNode;