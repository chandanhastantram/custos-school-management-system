import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";
import StatCard from "@/components/StatCard";
import {
  Users, GraduationCap, DollarSign, CheckSquare,
  BookOpen, Calendar, BarChart3, Clock, FileText, Brain
} from "lucide-react";
import type { UserRole } from "@/types";

const roleConfigs: Record<UserRole, { title: string; subtitle: string; stats: { label: string; value: string | number; change?: string; trend?: "up" | "down" | "neutral"; icon: typeof Users }[] }> = {
  super_admin: {
    title: "Platform Overview",
    subtitle: "System-wide metrics across all tenants",
    stats: [
      { label: "Total Students", value: "2,847", change: "+12%", trend: "up", icon: GraduationCap },
      { label: "Active Teachers", value: "186", change: "+3%", trend: "up", icon: Users },
      { label: "Attendance Today", value: "94.2%", change: "+1.5%", trend: "up", icon: CheckSquare },
      { label: "Revenue (Month)", value: "₹24.5L", change: "+8%", trend: "up", icon: DollarSign },
      { label: "Pending Fees", value: "₹3.2L", change: "-15%", trend: "down", icon: DollarSign },
      { label: "Active Courses", value: "142", trend: "neutral", icon: BookOpen },
    ],
  },
  principal: {
    title: "School Dashboard",
    subtitle: "Your school at a glance",
    stats: [
      { label: "Students Enrolled", value: "1,423", change: "+5%", trend: "up", icon: GraduationCap },
      { label: "Staff Members", value: "93", trend: "neutral", icon: Users },
      { label: "Today's Attendance", value: "96.1%", change: "+0.8%", trend: "up", icon: CheckSquare },
      { label: "Collection Rate", value: "87%", change: "+4%", trend: "up", icon: DollarSign },
      { label: "Upcoming Exams", value: "3", icon: FileText },
      { label: "Pending Approvals", value: "12", icon: Clock },
    ],
  },
  sub_admin: {
    title: "Admin Dashboard",
    subtitle: "Administrative operations overview",
    stats: [
      { label: "New Admissions", value: "28", change: "+10", trend: "up", icon: Users },
      { label: "Pending Requests", value: "15", icon: Clock },
      { label: "Today's Attendance", value: "95.3%", change: "+1.2%", trend: "up", icon: CheckSquare },
      { label: "Fee Collections", value: "₹4.8L", change: "+12%", trend: "up", icon: DollarSign },
    ],
  },
  teacher: {
    title: "My Dashboard",
    subtitle: "Your classes and schedule",
    stats: [
      { label: "My Classes", value: "5", icon: BookOpen },
      { label: "Students", value: "187", icon: GraduationCap },
      { label: "Attendance Marked", value: "3/5", icon: CheckSquare },
      { label: "Pending Grades", value: "42", icon: FileText },
      { label: "Upcoming Lessons", value: "8", icon: Calendar },
      { label: "AI Suggestions", value: "3", icon: Brain },
    ],
  },
  student: {
    title: "My Dashboard",
    subtitle: "Your academic overview",
    stats: [
      { label: "Attendance", value: "91%", change: "+2%", trend: "up", icon: CheckSquare },
      { label: "Courses Enrolled", value: "6", icon: BookOpen },
      { label: "Assignments Due", value: "3", icon: FileText },
      { label: "Activity Score", value: "78/100", change: "+5", trend: "up", icon: BarChart3 },
    ],
  },
  parent: {
    title: "Parent Dashboard",
    subtitle: "Your child's progress",
    stats: [
      { label: "Attendance", value: "91%", change: "+2%", trend: "up", icon: CheckSquare },
      { label: "Activity Score", value: "78/100", change: "+5", trend: "up", icon: BarChart3 },
      { label: "Pending Fees", value: "₹12,500", icon: DollarSign },
      { label: "Upcoming Events", value: "4", icon: Calendar },
    ],
  },
};

const Dashboard = () => {
  const { user, getPrimaryRole } = useAuthStore();
  if (!user) return <Navigate to="/login" replace />;

  const role = getPrimaryRole();
  const config = roleConfigs[role];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{config.title}</h1>
        <p className="text-muted-foreground">{config.subtitle}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {config.stats.map((stat, i) => (
          <StatCard key={stat.label} {...stat} index={i} />
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold mb-3">Recent Activity</h3>
          <div className="space-y-3">
            {[
              "Attendance marked for Class 10-A",
              "New student registration: Priya Sharma",
              "Fee payment received: ₹15,000",
              "Exam schedule published for Term 2",
            ].map((activity, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <div className="h-2 w-2 rounded-full bg-primary shrink-0" />
                <span className="text-muted-foreground">{activity}</span>
                <span className="text-xs text-muted-foreground/60 ml-auto shrink-0">{i + 1}h ago</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="font-semibold mb-3">Upcoming</h3>
          <div className="space-y-3">
            {[
              { event: "Staff Meeting", time: "Today, 3:00 PM" },
              { event: "Parent-Teacher Conference", time: "Tomorrow, 10:00 AM" },
              { event: "Term 2 Exams Begin", time: "Feb 15, 2026" },
              { event: "Annual Day Rehearsal", time: "Feb 20, 2026" },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span>{item.event}</span>
                <span className="text-xs text-muted-foreground">{item.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
