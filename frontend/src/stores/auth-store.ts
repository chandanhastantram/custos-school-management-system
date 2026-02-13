import { create } from "zustand";
import { persist } from "zustand/middleware";

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

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  setLoading: (loading: boolean) => void;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  getPrimaryRole: () => string;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: (token, refreshToken, user) => {
        set({ 
          token, 
          refreshToken, 
          user, 
          isAuthenticated: true 
        });
      },

      logout: () => {
        set({ 
          token: null, 
          refreshToken: null, 
          user: null, 
          isAuthenticated: false 
        });
      },

      setUser: (user) => set({ user }),

      setToken: (token) => set({ token }),

      setLoading: (isLoading) => set({ isLoading }),

      hasRole: (role) => get().user?.roles.includes(role) ?? false,

      hasAnyRole: (roles) => roles.some((r) => get().user?.roles.includes(r)) ?? false,

      getPrimaryRole: () => {
        const roles = get().user?.roles || [];
        const priority = ["super_admin", "principal", "sub_admin", "teacher", "student", "parent"];
        return priority.find((r) => roles.includes(r)) || "student";
      },
    }),
    {
      name: "custos-auth",
    }
  )
);
