import type { User, UserRole } from "@/types";

// Demo user data for the user management module
export const DEMO_USERS: User[] = [
  { id: "u-001", email: "admin@custos.school", first_name: "System", last_name: "Admin", roles: ["super_admin"], permissions: ["user:view", "user:create", "user:update", "user:delete", "user:manage_roles"], is_active: true },
  { id: "u-002", email: "sarah.johnson@demo.school", first_name: "Sarah", last_name: "Johnson", roles: ["principal"], permissions: ["user:view", "student:view", "teacher:view"], is_active: true },
  { id: "u-003", email: "james.wilson@demo.school", first_name: "James", last_name: "Wilson", roles: ["teacher"], permissions: ["student:view", "attendance:mark"], is_active: true },
  { id: "u-004", email: "alex.chen@demo.school", first_name: "Alex", last_name: "Chen", roles: ["student"], permissions: [], is_active: true },
  { id: "u-005", email: "maria.chen@demo.school", first_name: "Maria", last_name: "Chen", roles: ["parent"], permissions: [], is_active: true },
  { id: "u-006", email: "david.kumar@demo.school", first_name: "David", last_name: "Kumar", roles: ["sub_admin"], permissions: ["user:view", "user:create"], is_active: true },
  { id: "u-007", email: "priya.sharma@demo.school", first_name: "Priya", last_name: "Sharma", roles: ["teacher"], permissions: ["student:view", "attendance:mark"], is_active: true },
  { id: "u-008", email: "rahul.patel@demo.school", first_name: "Rahul", last_name: "Patel", roles: ["student"], permissions: [], is_active: true },
  { id: "u-009", email: "anita.rao@demo.school", first_name: "Anita", last_name: "Rao", roles: ["teacher"], permissions: ["student:view"], is_active: false },
  { id: "u-010", email: "suresh.nair@demo.school", first_name: "Suresh", last_name: "Nair", roles: ["parent"], permissions: [], is_active: true },
  { id: "u-011", email: "meena.iyer@demo.school", first_name: "Meena", last_name: "Iyer", roles: ["student"], permissions: [], is_active: true },
  { id: "u-012", email: "vikram.singh@demo.school", first_name: "Vikram", last_name: "Singh", roles: ["teacher"], permissions: ["student:view", "attendance:mark"], is_active: true },
];

export const ROLE_LABELS: Record<UserRole, string> = {
  super_admin: "Super Admin",
  principal: "Principal",
  sub_admin: "Sub Admin",
  teacher: "Teacher",
  student: "Student",
  parent: "Parent",
};

export const ROLE_VARIANT: Record<UserRole, "default" | "success" | "warning" | "info" | "purple" | "secondary"> = {
  super_admin: "default",
  principal: "purple",
  sub_admin: "info",
  teacher: "success",
  student: "warning",
  parent: "secondary",
};
