import { User, UserCreate, UserUpdate } from '@/types';

const API_BASE_URL = 'http://localhost:8001/api/v1';

class UserService {
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

  async getAllUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/users/`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch users: ${response.statusText}`);
    }

    return response.json();
  }

  async getUserById(userId: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch user: ${response.statusText}`);
    }

    return response.json();
  }

  async createUser(userData: UserCreate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to create user: ${error}`);
    }

    return response.json();
  }

  async updateUser(userId: string, userData: UserUpdate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to update user: ${error}`);
    }

    return response.json();
  }

  async deactivateUser(userId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to deactivate user: ${error}`);
    }
  }

  async getUsersByRole(role: User['role']): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/users/by-role/${role}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch users by role: ${response.statusText}`);
    }

    return response.json();
  }

  async getRoleCounts(): Promise<{ role_counts: Record<string, number>; total_users: number }> {
    const response = await fetch(`${API_BASE_URL}/users/role-counts`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch role counts: ${response.statusText}`);
    }

    return response.json();
  }

  async getAvailableRoles(): Promise<{ roles: Array<{ value: string; name: string; description: string }> }> {
    const response = await fetch(`${API_BASE_URL}/users/roles/available`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch available roles: ${response.statusText}`);
    }

    return response.json();
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch current user: ${response.statusText}`);
    }

    return response.json();
  }

  async updateCurrentUser(userData: UserUpdate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to update profile: ${error}`);
    }

    return response.json();
  }

  async changePassword(passwordData: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/users/me/change-password`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(passwordData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to change password: ${error}`);
    }

    return response.json();
  }

  async adminResetPassword(userId: string, passwordData: {
    new_password: string;
    confirm_password: string;
  }): Promise<{ message: string; user_email: string }> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/reset-password`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(passwordData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to reset password: ${error}`);
    }

    return response.json();
  }
}

export const userService = new UserService();