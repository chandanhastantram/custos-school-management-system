export type UserRole = "super_admin" | "principal" | "sub_admin" | "teacher" | "student" | "parent";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: UserRole[];
  permissions: string[];
  avatar_url?: string;
  is_active: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  primary_color?: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface StatCard {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon: string;
}
