import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Shield, LogOut, ChevronLeft, ChevronRight, Search, Bell, Sun, Moon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuthStore } from "@/stores/auth-store";
import { getNavForRole } from "@/lib/navigation";
import { NavLink } from "@/components/NavLink";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

const DashboardLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, tenant, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, setTheme } = useTheme();

  const navItems = getNavForRole(user?.roles || []);
  const initials = user ? `${user.first_name[0]}${user.last_name[0]}` : "?";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen flex w-full bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 flex flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300",
          collapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-14 border-b border-sidebar-border shrink-0">
          <Shield className="h-6 w-6 text-sidebar-primary shrink-0" />
          {!collapsed && (
            <span className="font-bold text-sidebar-primary-foreground tracking-tight">CUSTOS</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.url}
              to={item.url}
              end={item.url === "/dashboard"}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors",
                collapsed && "justify-center px-2"
              )}
              activeClassName="bg-sidebar-accent text-sidebar-primary"
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.title}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-sidebar-border p-3 space-y-2">
          {!collapsed && (
            <div className="flex items-center gap-2 px-1 mb-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-sidebar-accent text-sidebar-accent-foreground text-xs">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-sidebar-foreground truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-[10px] text-sidebar-foreground/60 truncate capitalize">
                  {user?.roles[0]?.replace("_", " ")}
                </p>
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className={cn(
              "w-full text-sidebar-foreground hover:bg-sidebar-accent hover:text-destructive",
              collapsed ? "px-2" : "justify-start"
            )}
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && <span className="ml-2">Sign Out</span>}
          </Button>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-16 h-6 w-6 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors shadow-sm"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </aside>

      {/* Main content */}
      <div className={cn("flex-1 flex flex-col transition-all duration-300", collapsed ? "ml-16" : "ml-60")}>
        {/* Top bar */}
        <header className="sticky top-0 z-20 h-14 border-b border-border bg-background/80 backdrop-blur-sm flex items-center gap-4 px-6">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search..." className="pl-9 h-9 bg-muted/50 border-0" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {tenant && (
              <span className="text-xs text-muted-foreground hidden sm:inline">{tenant.name}</span>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="relative overflow-hidden"
            >
              <Sun className="h-4 w-4 rotate-0 scale-100 transition-all duration-300 dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all duration-300 dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-primary rounded-full" />
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
