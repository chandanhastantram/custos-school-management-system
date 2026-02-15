/**
 * Authentication API Service
 */

import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  tenant_id: string;
  roles: string[];
  is_active: boolean;
  is_verified: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  tenant_slug: string;
}

export const authApi = {
  async login(credentials: LoginRequest, tenantId?: string): Promise<LoginResponse> {
    const config = tenantId ? { headers: { 'X-Tenant-ID': tenantId } } : {};
    
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      email: credentials.email,
      password: credentials.password,
    }, config);

    // Store tokens and user
    const { access_token, refresh_token, user } = response.data;
    useAuthStore.getState().login(access_token, refresh_token, user);

    return response.data;
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      useAuthStore.getState().logout();
    }
  },

  async refreshToken(refreshToken: string) {
    const response = await apiClient.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async forgotPassword(email: string) {
    const response = await apiClient.post('/auth/forgot-password', { email });
    return response.data;
  },

  async resetPassword(token: string, newPassword: string) {
    const response = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  async updateProfile(data: Partial<User>) {
    const response = await apiClient.patch<User>('/auth/profile', data);
    useAuthStore.getState().setUser(response.data);
    return response.data;
  },

  async changePassword(currentPassword: string, newPassword: string) {
    const response = await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};
