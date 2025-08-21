import { UserRole } from '@/utils/roles';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface RolePermissions {
  role: UserRole;
  permissions: string[];
}

export interface RoleInfo {
  role: UserRole;
  displayName: string;
  description: string;
  userCount: number;
  permissions: string[];
}

class RoleService {
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth-storage');
    if (token) {
      try {
        const parsed = JSON.parse(token);
        return {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${parsed.state.token}`,
        };
      } catch (e) {
        console.error('Failed to parse auth token:', e);
      }
    }
    return {
      'Content-Type': 'application/json',
    };
  }

  async getAllRoles(): Promise<RoleInfo[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch roles: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching roles:', error);
      throw error;
    }
  }

  async getRolePermissions(role: UserRole): Promise<string[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles/${role}/permissions`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch role permissions: ${response.statusText}`);
      }

      const data = await response.json();
      return data.permissions;
    } catch (error) {
      console.error('Error fetching role permissions:', error);
      throw error;
    }
  }

  async updateRolePermissions(role: UserRole, permissions: string[]): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles/${role}/permissions`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ permissions }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to update role permissions: ${error}`);
      }
    } catch (error) {
      console.error('Error updating role permissions:', error);
      throw error;
    }
  }

  async getAllPermissions(): Promise<{key: string; name: string; description: string; category: string}[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/permissions`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch permissions: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching permissions:', error);
      throw error;
    }
  }

  async getUserCountByRole(): Promise<Record<string, number>> {
    try {
      const response = await fetch(`${API_BASE_URL}/users/role-counts`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch user counts: ${response.statusText}`);
      }

      const data = await response.json();
      return data.role_counts;
    } catch (error) {
      console.error('Error fetching user counts:', error);
      throw error;
    }
  }

  async assignUserRole(userId: string, role: UserRole): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ role }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to assign role: ${error}`);
      }
    } catch (error) {
      console.error('Error assigning role:', error);
      throw error;
    }
  }

  async createCustomRole(roleData: {
    name: string;
    description: string;
    permissions: string[];
  }): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(roleData),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to create role: ${error}`);
      }
    } catch (error) {
      console.error('Error creating role:', error);
      throw error;
    }
  }

  async deleteCustomRole(role: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles/${role}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to delete role: ${error}`);
      }
    } catch (error) {
      console.error('Error deleting role:', error);
      throw error;
    }
  }

  async getRoleHierarchy(): Promise<Record<string, number>> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/roles/hierarchy`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch role hierarchy: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching role hierarchy:', error);
      throw error;
    }
  }
}

export const roleService = new RoleService();