/**
 * Debug Configuration Service
 *
 * Manages debug mode settings for development and testing purposes.
 * When debug mode is enabled, bypasses intent classification and agent assignment.
 */

export interface DebugConfig {
  enabled: boolean;
  selectedWorkflowTemplateId: string | null;
  selectedAgentTemplateId: string | null;
}

class DebugConfigService {
  private readonly storageKey = 'fuchsia-debug-config';

  /**
   * Get debug configuration from localStorage
   */
  getDebugConfig(): DebugConfig {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        return JSON.parse(stored);
      }
      return this.getDefaultConfig();
    } catch (error) {
      console.error('Failed to load debug config:', error);
      return this.getDefaultConfig();
    }
  }

  /**
   * Get default debug configuration
   */
  private getDefaultConfig(): DebugConfig {
    return {
      enabled: false,
      selectedWorkflowTemplateId: null,
      selectedAgentTemplateId: null,
    };
  }

  /**
   * Save debug configuration to localStorage
   */
  saveDebugConfig(config: Partial<DebugConfig>): void {
    try {
      const current = this.getDebugConfig();
      const updated = { ...current, ...config };
      localStorage.setItem(this.storageKey, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save debug config:', error);
    }
  }

  /**
   * Enable debug mode
   */
  enableDebugMode(): void {
    this.saveDebugConfig({ enabled: true });
  }

  /**
   * Disable debug mode
   */
  disableDebugMode(): void {
    this.saveDebugConfig({ enabled: false });
  }

  /**
   * Check if debug mode is enabled
   */
  isDebugMode(): boolean {
    return this.getDebugConfig().enabled;
  }

  /**
   * Set selected workflow template
   */
  setWorkflowTemplate(templateId: string | null): void {
    this.saveDebugConfig({ selectedWorkflowTemplateId: templateId });
  }

  /**
   * Set selected agent template
   */
  setAgentTemplate(templateId: string | null): void {
    this.saveDebugConfig({ selectedAgentTemplateId: templateId });
  }

  /**
   * Get selected workflow template ID
   */
  getSelectedWorkflowTemplateId(): string | null {
    return this.getDebugConfig().selectedWorkflowTemplateId;
  }

  /**
   * Get selected agent template ID
   */
  getSelectedAgentTemplateId(): string | null {
    return this.getDebugConfig().selectedAgentTemplateId;
  }

  /**
   * Clear debug configuration
   */
  clearDebugConfig(): void {
    try {
      localStorage.removeItem(this.storageKey);
    } catch (error) {
      console.error('Failed to clear debug config:', error);
    }
  }

  /**
   * Validate debug configuration
   * Returns true if debug mode is enabled and both selections are made
   */
  isValidDebugConfig(): boolean {
    const config = this.getDebugConfig();
    return (
      config.enabled &&
      config.selectedWorkflowTemplateId !== null &&
      config.selectedAgentTemplateId !== null
    );
  }
}

export const debugConfigService = new DebugConfigService();
