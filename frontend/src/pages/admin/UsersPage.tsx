import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search, Plus, MoreHorizontal, Filter, Download, Loader2,
  Edit, Trash2, UserCheck, UserX, RefreshCw, AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { DEMO_USERS, ROLE_LABELS, ROLE_VARIANT } from "@/data/demo-users";
import UserFormDialog from "@/components/users/UserFormDialog";
import apiClient, { ApiError } from "@/lib/api-client";
import type { User, UserRole } from "@/types";
import { toast } from "@/hooks/use-toast";

// API types
interface UserApiResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar?: string;
  status: string;
  roles: string[];
  created_at: string;
  last_login_at?: string;
}

interface UsersListResponse {
  items: UserApiResponse[];
  total: number;
  page: number;
  size: number;
}

// Transform API response to frontend User type
const transformApiUser = (apiUser: UserApiResponse): User => ({
  id: apiUser.id,
  email: apiUser.email,
  first_name: apiUser.first_name,
  last_name: apiUser.last_name,
  roles: apiUser.roles as UserRole[],
  permissions: [],
  is_active: apiUser.status === "active",
});

// API functions
const fetchUsers = async (params: {
  search?: string;
  status?: string;
  page?: number;
  size?: number;
}): Promise<UsersListResponse> => {
  const queryParams = new URLSearchParams();
  if (params.search) queryParams.set("search", params.search);
  if (params.status && params.status !== "all") queryParams.set("status", params.status);
  queryParams.set("page", String(params.page || 1));
  queryParams.set("size", String(params.size || 50));
  
  return apiClient.get<UsersListResponse>(`/users?${queryParams.toString()}`);
};

const createUser = async (data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role_ids?: string[];
}): Promise<UserApiResponse> => {
  return apiClient.post<UserApiResponse>("/users", data);
};

const updateUser = async (userId: string, data: {
  first_name?: string;
  last_name?: string;
  status?: string;
}): Promise<UserApiResponse> => {
  return apiClient.put<UserApiResponse>(`/users/${userId}`, data);
};

const deleteUser = async (userId: string): Promise<void> => {
  await apiClient.delete(`/users/${userId}`);
};

const UsersPage = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [demoUsers, setDemoUsers] = useState<User[]>(DEMO_USERS);

  // Fetch users from API
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["users", search, statusFilter],
    queryFn: () => fetchUsers({ search, status: statusFilter }),
    retry: 1,
    staleTime: 30000,
  });

  // Handle API error - switch to demo mode
  const users = demoMode
    ? demoUsers
    : (data?.items.map(transformApiUser) || []);

  // If API fails, enable demo mode
  if (isError && !demoMode) {
    console.log("API unavailable, switching to demo mode", error);
    setDemoMode(true);
  }

  // Filter users (for demo mode or client-side role filtering)
  const filtered = users.filter((u) => {
    const matchesSearch = demoMode
      ? `${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(search.toLowerCase())
      : true; // API already filtered
    const matchesRole = roleFilter === "all" || u.roles.includes(roleFilter as UserRole);
    const matchesStatus = demoMode
      ? statusFilter === "all" ||
        (statusFilter === "active" && u.is_active) ||
        (statusFilter === "inactive" && !u.is_active)
      : true; // API already filtered
    return matchesSearch && matchesRole && matchesStatus;
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast({ title: "User created", description: "New user has been added." });
      setDialogOpen(false);
    },
    onError: (err: ApiError) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: Parameters<typeof updateUser>[1] }) =>
      updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast({ title: "User updated" });
      setDialogOpen(false);
    },
    onError: (err: ApiError) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast({ title: "User removed", variant: "destructive" });
    },
    onError: (err: ApiError) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const handleCreate = () => {
    setEditingUser(null);
    setDialogOpen(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setDialogOpen(true);
  };

  const handleSave = (data: Omit<User, "id" | "permissions">) => {
    if (demoMode) {
      // Demo mode - local state
      if (editingUser) {
        setDemoUsers((prev) =>
          prev.map((u) => (u.id === editingUser.id ? { ...u, ...data } : u))
        );
        toast({ title: "User updated", description: `${data.first_name} ${data.last_name} has been updated.` });
      } else {
        const newUser: User = {
          ...data,
          id: `u-${Date.now()}`,
          permissions: [],
        };
        setDemoUsers((prev) => [newUser, ...prev]);
        toast({ title: "User created", description: `${data.first_name} ${data.last_name} has been added.` });
      }
      setDialogOpen(false);
    } else {
      // Real API
      if (editingUser) {
        updateMutation.mutate({
          userId: editingUser.id,
          data: {
            first_name: data.first_name,
            last_name: data.last_name,
          },
        });
      } else {
        createMutation.mutate({
          email: data.email,
          password: "TempPass@123", // Would need password field in form
          first_name: data.first_name,
          last_name: data.last_name,
        });
      }
    }
  };

  const handleDelete = (user: User) => {
    if (demoMode) {
      setDemoUsers((prev) => prev.filter((u) => u.id !== user.id));
      toast({ title: "User removed", description: `${user.first_name} ${user.last_name} has been removed.`, variant: "destructive" });
    } else {
      deleteMutation.mutate(user.id);
    }
  };

  const handleToggleStatus = (user: User) => {
    if (demoMode) {
      setDemoUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, is_active: !u.is_active } : u))
      );
      toast({ title: user.is_active ? "User deactivated" : "User activated" });
    } else {
      updateMutation.mutate({
        userId: user.id,
        data: { status: user.is_active ? "inactive" : "active" },
      });
    }
  };

  const totalCount = demoMode ? demoUsers.length : (data?.total || 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">User Management</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">{totalCount} total users · {filtered.length} shown</p>
        </div>
        <div className="flex items-center gap-2">
          {!demoMode && (
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
          )}
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm" onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-1" /> Add User
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {isError && !demoMode && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">Unable to connect to server. Showing demo data.</span>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setDemoMode(true)}>
            Use Demo Mode
          </Button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={roleFilter} onValueChange={setRoleFilter}>
          <SelectTrigger className="w-[160px]">
            <Filter className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            {(Object.keys(ROLE_LABELS) as UserRole[]).map((role) => (
              <SelectItem key={role} value={role}>{ROLE_LABELS[role]}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-border bg-card overflow-hidden"
      >
        {isLoading && !demoMode ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40">
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((user, i) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-border hover:bg-muted/30 transition-colors"
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
                            {user.first_name[0]}{user.last_name[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-sm">{user.first_name} {user.last_name}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {user.roles.map((role) => (
                          <Badge key={role} variant={ROLE_VARIANT[role]} className="text-[10px]">
                            {ROLE_LABELS[role]}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <span className={`h-2 w-2 rounded-full ${user.is_active ? "bg-emerald-500" : "bg-muted-foreground/40"}`} />
                        <span className="text-sm">{user.is_active ? "Active" : "Inactive"}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEdit(user)}>
                            <Edit className="h-3.5 w-3.5 mr-2" /> Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleToggleStatus(user)}>
                            {user.is_active ? (
                              <><UserX className="h-3.5 w-3.5 mr-2" /> Deactivate</>
                            ) : (
                              <><UserCheck className="h-3.5 w-3.5 mr-2" /> Activate</>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleDelete(user)} className="text-destructive focus:text-destructive">
                            <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </motion.tr>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </motion.div>

      <UserFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        user={editingUser}
        onSave={handleSave}
      />
    </div>
  );
};

export default UsersPage;
