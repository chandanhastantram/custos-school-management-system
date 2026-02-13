import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { GraduationCap, ArrowRight, Loader2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";
import apiClient, { ApiError } from "@/lib/api-client";
import type { Tenant, UserRole } from "@/types";

// Demo tenants and users for frontend demo (fallback when backend unavailable)
const DEMO_TENANTS: Record<string, Tenant> = {
  "demo-school": {
    id: "t-001",
    name: "Demo International School",
    slug: "demo-school",
    logo_url: undefined,
    primary_color: "#f97316",
    is_active: true,
  },
};

const DEMO_USERS: Record<string, { password: string; user: { id: string; email: string; first_name: string; last_name: string; roles: UserRole[]; permissions: string[]; is_active: boolean } }> = {
  "admin@custos.school": {
    password: "Admin@123",
    user: {
      id: "u-001", email: "admin@custos.school", first_name: "System", last_name: "Admin",
      roles: ["super_admin"], permissions: ["user:view", "user:create", "user:update", "user:delete", "user:manage_roles", "analytics:view_admin"],
      is_active: true,
    },
  },
  "principal@demo.school": {
    password: "Admin@123",
    user: {
      id: "u-002", email: "principal@demo.school", first_name: "Sarah", last_name: "Johnson",
      roles: ["principal"], permissions: ["user:view", "student:view", "teacher:view", "analytics:view_admin", "attendance:view", "attendance:report"],
      is_active: true,
    },
  },
  "teacher@demo.school": {
    password: "Admin@123",
    user: {
      id: "u-003", email: "teacher@demo.school", first_name: "James", last_name: "Wilson",
      roles: ["teacher"], permissions: ["student:view", "attendance:mark", "attendance:view", "analytics:view_teacher"],
      is_active: true,
    },
  },
  "student@demo.school": {
    password: "Admin@123",
    user: {
      id: "u-004", email: "student@demo.school", first_name: "Alex", last_name: "Chen",
      roles: ["student"], permissions: ["analytics:view_student"],
      is_active: true,
    },
  },
  "parent@demo.school": {
    password: "Admin@123",
    user: {
      id: "u-005", email: "parent@demo.school", first_name: "Maria", last_name: "Chen",
      roles: ["parent"], permissions: ["analytics:view_student"],
      is_active: true,
    },
  },
};

// API response types
interface TenantPublicInfo {
  exists: boolean;
  id?: string;
  name?: string;
  logo?: string;
  primary_color?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface UserMeResponse {
  id: string;
  tenant_id: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  permissions: string[];
}

const Login = () => {
  const [step, setStep] = useState<"slug" | "credentials">("slug");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [tenant, setTenantLocal] = useState<Tenant | null>(null);
  const [useDemo, setUseDemo] = useState(false);

  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSlugSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Try real API first
      const response = await apiClient.get<TenantPublicInfo>(`/tenants/by-slug/${slug.toLowerCase()}`);
      
      if (response.data.exists && response.data.id) {
        const tenantData: Tenant = {
          id: response.data.id,
          name: response.data.name || slug,
          slug: slug.toLowerCase(),
          logo_url: response.data.logo,
          primary_color: response.data.primary_color || "#f97316",
          is_active: true,
        };
        setTenantLocal(tenantData);
        setUseDemo(false);
        setStep("credentials");
      } else {
        setError("School not found. Check your school ID.");
      }
    } catch (err) {
      // Fallback to demo mode if API unavailable
      console.log("API unavailable, using demo mode", err);
      const found = DEMO_TENANTS[slug.toLowerCase()];
      if (found) {
        setTenantLocal(found);
        setUseDemo(true);
        setStep("credentials");
      } else {
        setError("School not found. Try 'demo-school' for demo mode.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (useDemo) {
      // Demo mode login
      setTimeout(() => {
        const demoUser = DEMO_USERS[email.toLowerCase()];
        if (demoUser && demoUser.password === password) {
          const user: any = {
            ...demoUser.user,
            username: demoUser.user.email.split('@')[0],
            full_name: `${demoUser.user.first_name} ${demoUser.user.last_name}`,
            tenant_id: tenant!.id,
            is_verified: true,
          };
          console.log("Demo login - setting user:", user);
          login("demo-token", "demo-refresh", user);
          
          // Wait a bit for state to persist before navigating
          setTimeout(() => {
            console.log("After login, auth state:", useAuthStore.getState());
            console.log("isAuthenticated:", useAuthStore.getState().isAuthenticated);
            navigate("/dashboard");
          }, 200);
        } else {
          setError("Invalid credentials. Try admin@custos.school / Admin@123");
        }
        setLoading(false);
      }, 500);
      return;
    }

    try {
      // Real API login
      const tokenResponse = await apiClient.post<TokenResponse>("/auth/login", {
        email: email.toLowerCase(),
        password,
        remember_me: false,
      });

      // Fetch user details
      const userResponse = await apiClient.get<UserMeResponse>("/auth/me", {
        headers: {
          Authorization: `Bearer ${tokenResponse.data.access_token}`,
          'X-Tenant-ID': tenant!.id,
        }
      });

      const user: any = {
        id: userResponse.data.id,
        email: userResponse.data.email,
        username: userResponse.data.email.split('@')[0],
        full_name: `${userResponse.data.first_name} ${userResponse.data.last_name}`,
        tenant_id: userResponse.data.tenant_id,
        roles: userResponse.data.roles,
        is_active: true,
        is_verified: true,
      };

      login(tokenResponse.data.access_token, tokenResponse.data.refresh_token, user);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Login failed. Please check your credentials.");
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 gradient-primary relative items-center justify-center p-12">
        <div className="relative z-10 text-primary-foreground max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-3 rounded-xl bg-primary-foreground/10 backdrop-blur">
              <Shield className="h-8 w-8" />
            </div>
            <span className="text-2xl font-bold tracking-tight">CUSTOS</span>
          </div>
          <h1 className="text-4xl font-bold mb-4 leading-tight">
            Smart School Management, Simplified.
          </h1>
          <p className="text-primary-foreground/80 text-lg leading-relaxed">
            Track operations, manage academics, and empower educators with a unified platform.
          </p>
        </div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.1),transparent_70%)]" />
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <GraduationCap className="h-7 w-7 text-primary" />
            <span className="text-xl font-bold">CUSTOS</span>
          </div>

          <AnimatePresence mode="wait">
            {step === "slug" ? (
              <motion.div
                key="slug"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
              >
                <h2 className="text-2xl font-bold mb-1">Find your school</h2>
                <p className="text-muted-foreground mb-8">Enter your school's unique identifier to get started.</p>

                <form onSubmit={handleSlugSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="slug">School ID</Label>
                    <Input
                      id="slug"
                      placeholder="e.g. demo-school"
                      value={slug}
                      onChange={(e) => setSlug(e.target.value)}
                      className="h-11"
                      autoFocus
                    />
                  </div>

                  {error && (
                    <p className="text-sm text-destructive">{error}</p>
                  )}

                  <Button type="submit" className="w-full h-11" disabled={!slug || loading}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Continue
                    {!loading && <ArrowRight className="h-4 w-4 ml-2" />}
                  </Button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="creds"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
              >
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-2xl font-bold">{tenant?.name}</h2>
                  {useDemo && (
                    <span className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 px-2 py-0.5 rounded-full">
                      Demo Mode
                    </span>
                  )}
                </div>
                <p className="text-muted-foreground mb-8">Sign in to your account.</p>

                <form onSubmit={handleLogin} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@school.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="h-11"
                      autoFocus
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password">Password</Label>
                      <Button variant="link" className="p-0 h-auto text-xs" type="button">
                        Forgot password?
                      </Button>
                    </div>
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-11"
                    />
                  </div>

                  {error && (
                    <p className="text-sm text-destructive">{error}</p>
                  )}

                  <Button type="submit" className="w-full h-11" disabled={!email || !password || loading}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Sign In
                  </Button>

                  <Button
                    variant="ghost"
                    type="button"
                    className="w-full text-sm text-muted-foreground"
                    onClick={() => { setStep("slug"); setError(""); }}
                  >
                    ← Different school
                  </Button>
                </form>

                {/* Demo accounts helper */}
                {useDemo && (
                  <div className="mt-6 p-4 rounded-lg bg-muted/50 border border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-2">Demo Accounts:</p>
                    <div className="space-y-1 text-xs text-muted-foreground">
                      <p><span className="font-mono">admin@custos.school</span> — Super Admin</p>
                      <p><span className="font-mono">principal@demo.school</span> — Principal</p>
                      <p><span className="font-mono">teacher@demo.school</span> — Teacher</p>
                      <p><span className="font-mono">student@demo.school</span> — Student</p>
                      <p className="text-muted-foreground/60 mt-1">Password: <span className="font-mono">Admin@123</span></p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default Login;
