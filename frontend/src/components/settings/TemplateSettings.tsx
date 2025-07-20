import React, { useState, useEffect } from 'react';
import { templateService, TemplateSettings } from '@/services/templateService';
import { FolderOpen, Save, RotateCcw } from 'lucide-react';

export const TemplateSettingsComponent: React.FC = () => {
  const [settings, setSettings] = useState<TemplateSettings>(templateService.getTemplateSettings());
  const [hasChanges, setHasChanges] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const current = templateService.getTemplateSettings();
    setSettings(current);
  }, []);

  const handleSettingChange = (key: keyof TemplateSettings, value: string | boolean) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
    setSuccess(null);
  };

  const handleSave = () => {
    templateService.saveTemplateSettings(settings);
    setHasChanges(false);
    setSuccess('Template settings saved successfully!');
    
    // Clear success message after 3 seconds
    setTimeout(() => setSuccess(null), 3000);
  };

  const handleReset = () => {
    const defaultSettings = {
      defaultTemplatesFolder: './templates/workflows',
      customTemplatesFolder: './templates/custom',
      autoSaveEnabled: true,
      templateFileExtension: '.json',
    };
    setSettings(defaultSettings);
    setHasChanges(true);
    setSuccess(null);
  };

  const handleBrowseFolder = (settingKey: 'defaultTemplatesFolder' | 'customTemplatesFolder') => {
    // In a real application, this would open a folder browser dialog
    // For now, we'll just provide a text input
    const newPath = prompt(`Enter path for ${settingKey}:`, settings[settingKey]);
    if (newPath && newPath !== settings[settingKey]) {
      handleSettingChange(settingKey, newPath);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Template Settings</h2>
        {hasChanges && (
          <div className="flex space-x-2">
            <button
              onClick={handleReset}
              className="flex items-center space-x-1 px-3 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={handleSave}
              className="flex items-center space-x-1 px-3 py-2 bg-fuschia-500 text-white rounded-md hover:bg-fuschia-600"
            >
              <Save className="w-4 h-4" />
              <span>Save Changes</span>
            </button>
          </div>
        )}
      </div>

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800">{success}</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          {/* Default Templates Folder */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Templates Folder
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={settings.defaultTemplatesFolder}
                onChange={(e) => handleSettingChange('defaultTemplatesFolder', e.target.value)}
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                placeholder="./templates/workflows"
              />
              <button
                onClick={() => handleBrowseFolder('defaultTemplatesFolder')}
                className="flex items-center space-x-1 px-3 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                <FolderOpen className="w-4 h-4" />
                <span>Browse</span>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Folder where built-in workflow templates are stored
            </p>
          </div>

          {/* Custom Templates Folder */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Custom Templates Folder
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={settings.customTemplatesFolder}
                onChange={(e) => handleSettingChange('customTemplatesFolder', e.target.value)}
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
                placeholder="./templates/custom"
              />
              <button
                onClick={() => handleBrowseFolder('customTemplatesFolder')}
                className="flex items-center space-x-1 px-3 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                <FolderOpen className="w-4 h-4" />
                <span>Browse</span>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Folder where user-created templates are saved
            </p>
          </div>

          {/* Template File Extension */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template File Extension
            </label>
            <select
              value={settings.templateFileExtension}
              onChange={(e) => handleSettingChange('templateFileExtension', e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-fuschia-500"
            >
              <option value=".json">.json</option>
              <option value=".yaml">.yaml</option>
              <option value=".yml">.yml</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              File extension used for template files
            </p>
          </div>

          {/* Auto Save */}
          <div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoSaveEnabled"
                checked={settings.autoSaveEnabled}
                onChange={(e) => handleSettingChange('autoSaveEnabled', e.target.checked)}
                className="h-4 w-4 text-fuschia-600 focus:ring-fuschia-500 border-gray-300 rounded"
              />
              <label htmlFor="autoSaveEnabled" className="ml-2 block text-sm text-gray-900">
                Enable Auto-Save for Templates
              </label>
            </div>
            <p className="text-xs text-gray-500 mt-1 ml-6">
              Automatically save templates when changes are made in the designer
            </p>
          </div>
        </div>
      </div>

      {/* Template Management Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Template Management</h4>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• Templates can be loaded into the Process Designer using the Load button</p>
          <p>• Use the "Use Template" button in Workflow Templates to load templates directly</p>
          <p>• Custom templates are automatically saved to your browser's local storage</p>
          <p>• Export templates as files to share with other users or backup your work</p>
        </div>
      </div>
    </div>
  );
};