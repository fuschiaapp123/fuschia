export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'analyst' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface KnowledgeNode {
  id: string;
  name: string;
  type: 'entity' | 'process' | 'system' | 'document' | 'person' | 'department';
  properties: Record<string, unknown>;
  description?: string;
  created_at: string;
  updated_at?: string;
  created_by: string;
}

export interface KnowledgeRelationship {
  id: string;
  from_node_id: string;
  to_node_id: string;
  type: 'belongs_to' | 'manages' | 'requires' | 'produces' | 'interacts_with' | 'depends_on';
  properties: Record<string, unknown>;
  weight: number;
  created_at: string;
  created_by: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeNode[];
  relationships: KnowledgeRelationship[];
  metadata: Record<string, unknown>;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface AppState {
  sidebarCollapsed: boolean;
  activeTab: string;
  currentModule: 'knowledge' | 'workflow' | 'agents' | 'analytics' | 'settings';
}