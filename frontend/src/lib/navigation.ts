import type { UserRole } from "@/types";
import {
  LayoutDashboard, Users, GraduationCap, Calendar, ClipboardList,
  DollarSign, BarChart3, HelpCircle, MessageSquare, FileText,
  BookOpen, Clock, Brain, Settings, Bell, CheckSquare, School,
  Book, Bus, Sparkles
} from "lucide-react";

export interface NavItem {
  title: string;
  url: string;
  icon: typeof LayoutDashboard;
  roles: UserRole[];
  permission?: string;
  children?: NavItem[];
}

export const navigationItems: NavItem[] = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard, roles: ["super_admin", "principal", "sub_admin", "teacher", "student", "parent"] },
  { title: "Users", url: "/admin/users", icon: Users, roles: ["super_admin", "principal", "sub_admin"] },
  { title: "Academics", url: "/admin/academics", icon: School, roles: ["super_admin", "principal", "sub_admin"] },
  { title: "Scheduling", url: "/admin/scheduling", icon: Clock, roles: ["super_admin", "principal", "sub_admin", "teacher"] },
  { title: "Attendance", url: "/admin/attendance", icon: CheckSquare, roles: ["super_admin", "principal", "sub_admin", "teacher"] },
  { title: "My Classes", url: "/teacher/classes", icon: BookOpen, roles: ["teacher"] },
  { title: "Grading", url: "/teacher/grading", icon: ClipboardList, roles: ["teacher"] },
  { title: "My Courses", url: "/student/courses", icon: BookOpen, roles: ["student"] },
  { title: "Assignments", url: "/student/assignments", icon: FileText, roles: ["student"] },
  { title: "My Results", url: "/student/results", icon: BarChart3, roles: ["student"] },
  { title: "Timetable", url: "/student/timetable", icon: Calendar, roles: ["student"] },
  { title: "Child Progress", url: "/parent/progress", icon: BarChart3, roles: ["parent"] },
  { title: "Finance", url: "/admin/finance", icon: DollarSign, roles: ["super_admin", "principal", "sub_admin", "parent"] },
  { title: "Library", url: "/admin/library", icon: Book, roles: ["super_admin", "principal", "sub_admin", "student"] },
  { title: "Transport", url: "/admin/transport", icon: Bus, roles: ["super_admin", "principal", "sub_admin"] },
  { title: "Examinations", url: "/admin/exams", icon: GraduationCap, roles: ["super_admin", "principal", "sub_admin", "teacher"] },
  { title: "Analytics", url: "/admin/analytics", icon: BarChart3, roles: ["super_admin", "principal"] },
  { title: "Messages", url: "/messages", icon: MessageSquare, roles: ["super_admin", "principal", "sub_admin", "teacher", "student", "parent"] },
  { title: "Helpdesk", url: "/helpdesk", icon: HelpCircle, roles: ["super_admin", "principal", "sub_admin", "teacher", "student", "parent"] },
  { title: "AI Assistant", url: "/ai", icon: Brain, roles: ["teacher", "student"] },
  { title: "AI Quiz Trainer", url: "/student/ai-trainer", icon: Sparkles, roles: ["student"] },
  { title: "AI Tutor", url: "/student/study-trainer", icon: GraduationCap, roles: ["student"] },
  { title: "Notifications", url: "/notifications", icon: Bell, roles: ["super_admin", "principal", "sub_admin", "teacher", "student", "parent"] },
  { title: "Settings", url: "/settings", icon: Settings, roles: ["super_admin", "principal"] },
];

export function getNavForRole(roles: UserRole[]): NavItem[] {
  return navigationItems.filter((item) => item.roles.some((r) => roles.includes(r)));
}
