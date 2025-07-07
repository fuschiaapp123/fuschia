import { create } from 'zustand';
import { AppState } from '@/types';
import { ReactFlowData } from '@/utils/yamlParser';

interface AppStore extends AppState {
  workflowData: ReactFlowData | null;
  agentData: ReactFlowData | null;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setActiveTab: (tab: string) => void;
  setCurrentModule: (module: 'knowledge' | 'workflow' | 'agents' | 'analytics' | 'settings') => void;
  setWorkflowData: (data: ReactFlowData | null) => void;
  setAgentData: (data: ReactFlowData | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  sidebarCollapsed: false,
  activeTab: 'overview',
  currentModule: 'knowledge',
  workflowData: null,
  agentData: null,
  
  setSidebarCollapsed: (collapsed: boolean) => set({ sidebarCollapsed: collapsed }),
  
  setActiveTab: (tab: string) => set({ activeTab: tab }),
  
  setCurrentModule: (module: 'knowledge' | 'workflow' | 'agents' | 'analytics' | 'settings') => 
    set({ currentModule: module }),
  
  setWorkflowData: (data: ReactFlowData | null) => set({ workflowData: data }),
  
  setAgentData: (data: ReactFlowData | null) => set({ agentData: data }),
}));