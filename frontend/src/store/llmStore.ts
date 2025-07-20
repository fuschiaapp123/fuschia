import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { LLMSettings } from '@/types/llm';
import { getDefaultSettings } from '@/config/llmProviders';

interface LLMStore extends LLMSettings {
  updateProvider: (provider: string) => void;
  updateModel: (model: string) => void;
  updateApiKey: (provider: string, apiKey: string) => void;
  updateTemperature: (temperature: number) => void;
  updateMaxTokens: (maxTokens: number) => void;
  updateStreamingEnabled: (enabled: boolean) => void;
  resetToDefaults: () => void;
  getApiKey: (provider: string) => string | undefined;
}

export const useLLMStore = create<LLMStore>()(
  persist(
    (set, get) => ({
      ...getDefaultSettings(),
      
      updateProvider: (provider: string) => 
        set((state) => ({ 
          selectedProvider: provider,
          // Reset to first model of new provider
          selectedModel: '' // Will be set by the component
        })),
      
      updateModel: (model: string) => 
        set({ selectedModel: model }),
      
      updateApiKey: (provider: string, apiKey: string) => 
        set((state) => ({
          apiKeys: {
            ...state.apiKeys,
            [provider]: apiKey
          }
        })),
      
      updateTemperature: (temperature: number) => 
        set({ temperature }),
      
      updateMaxTokens: (maxTokens: number) => 
        set({ maxTokens }),
      
      updateStreamingEnabled: (enabled: boolean) => 
        set({ streamingEnabled: enabled }),
      
      resetToDefaults: () => 
        set(getDefaultSettings()),
      
      getApiKey: (provider: string) => {
        const state = get();
        return state.apiKeys[provider];
      }
    }),
    {
      name: 'llm-settings',
      partialize: (state) => ({
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel,
        apiKeys: state.apiKeys,
        temperature: state.temperature,
        maxTokens: state.maxTokens,
        streamingEnabled: state.streamingEnabled
      })
    }
  )
);