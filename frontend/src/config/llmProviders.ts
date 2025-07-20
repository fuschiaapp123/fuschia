import { LLMProvider } from '@/types/llm';

export const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT models from OpenAI',
    apiKeyRequired: true,
    baseUrl: 'https://api.openai.com/v1',
    icon: '🤖',
    models: [
      {
        id: 'gpt-4o',
        name: 'GPT-4o',
        description: 'Most advanced model with multimodal capabilities',
        contextWindow: 128000,
        pricing: { input: 0.005, output: 0.015 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      },
      {
        id: 'gpt-4-turbo',
        name: 'GPT-4 Turbo',
        description: 'Latest GPT-4 model with improved performance',
        contextWindow: 128000,
        pricing: { input: 0.01, output: 0.03 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      },
      {
        id: 'gpt-4',
        name: 'GPT-4',
        description: 'High-intelligence flagship model',
        contextWindow: 8192,
        pricing: { input: 0.03, output: 0.06 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          streaming: true
        }
      },
      {
        id: 'gpt-3.5-turbo',
        name: 'GPT-3.5 Turbo',
        description: 'Fast, capable model for most tasks',
        contextWindow: 16384,
        pricing: { input: 0.001, output: 0.002 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          streaming: true
        }
      }
    ]
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude models from Anthropic',
    apiKeyRequired: true,
    baseUrl: 'https://api.anthropic.com/v1',
    icon: '🎭',
    models: [
      {
        id: 'claude-3-5-sonnet-20241022',
        name: 'Claude 3.5 Sonnet',
        description: 'Most intelligent model with best performance',
        contextWindow: 200000,
        pricing: { input: 0.003, output: 0.015 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      },
      {
        id: 'claude-3-opus-20240229',
        name: 'Claude 3 Opus',
        description: 'Powerful model for complex tasks',
        contextWindow: 200000,
        pricing: { input: 0.015, output: 0.075 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      },
      {
        id: 'claude-3-sonnet-20240229',
        name: 'Claude 3 Sonnet',
        description: 'Balanced intelligence and speed',
        contextWindow: 200000,
        pricing: { input: 0.003, output: 0.015 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      },
      {
        id: 'claude-3-haiku-20240307',
        name: 'Claude 3 Haiku',
        description: 'Fast and cost-effective',
        contextWindow: 200000,
        pricing: { input: 0.00025, output: 0.00125 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      }
    ]
  },
  {
    id: 'xai',
    name: 'xAI',
    description: 'Grok models from xAI',
    apiKeyRequired: true,
    baseUrl: 'https://api.x.ai/v1',
    icon: '🚀',
    models: [
      {
        id: 'grok-beta',
        name: 'Grok Beta',
        description: 'Latest Grok model with real-time information',
        contextWindow: 131072,
        pricing: { input: 0.005, output: 0.015 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          streaming: true
        }
      },
      {
        id: 'grok-vision-beta',
        name: 'Grok Vision Beta',
        description: 'Grok with vision capabilities',
        contextWindow: 131072,
        pricing: { input: 0.005, output: 0.015 },
        capabilities: {
          chat: true,
          completion: true,
          functionCalling: true,
          vision: true,
          streaming: true
        }
      }
    ]
  }
];

export const getProviderById = (id: string): LLMProvider | undefined => {
  return LLM_PROVIDERS.find(provider => provider.id === id);
};

export const getModelById = (providerId: string, modelId: string) => {
  const provider = getProviderById(providerId);
  return provider?.models.find(model => model.id === modelId);
};

export const getDefaultSettings = () => ({
  selectedProvider: 'openai',
  selectedModel: 'gpt-3.5-turbo',
  apiKeys: {},
  temperature: 0.7,
  maxTokens: 4000,
  streamingEnabled: true
});