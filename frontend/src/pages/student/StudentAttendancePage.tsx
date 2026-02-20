import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CalendarCheck, TrendingUp, BookOpen, Clock,
  CheckCircle2, XCircle, AlertCircle, RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { studentApi } from "@/services/student-api";
import { cn } from "@/lib/utils";

// Demo data (fallback)
const DEMO_OVERALL = { total: 220, present: 198, absent: 14, late: 8, percentage: 90 };
const DEMO_SUBJECTS = [
  { name: "Mathematics", total: 40, present: 38, percentage: 95 },
  { name: "Science", total: 40, present: 36, percentage: 90 },
  { name: "English", total: 36, present: 30, percentage: 83 },
  { name: "Hindi", total: 32, present: 30, percentage: 94 },
  { name: "Social Science", total: 36, present: 32, percentage: 89 },
  { name: "Computer Science", total: 20, present: 18, percentage: 90 },
];
const DEMO_RECENT = [
  { date: "2024-02-12", subject: "Mathematics", status: "present" },
  { date: "2024-02-12", subject: "Science", status: "present" },
  { date: "2024-02-11", subject: "English", status: "absent" },
  { date: "2024-02-11", subject: "Hindi", status: "present" },
  { date: "2024-02-10", subject: "Mathematics", status: "late" },
  { date: "2024-02-10", subject: "Social Science", status: "present" },
];

const StudentAttendancePage = () => {
  const [demoMode, setDemoMode] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["student-attendance"],
    queryFn: () => studentApi.getAttendance(),
    retry: 1,
    staleTime: 30000,
  });

  useEffect(() => {
    if (isError && !demoMode) setDemoMode(true);
  }, [isError, demoMode]);

  const overall = demoMode ? DEMO_OVERALL : (data?.overall || DEMO_OVERALL);
  const subjects = demoMode ? DEMO_SUBJECTS : (data?.subjects || DEMO_SUBJECTS);
  const recent = demoMode ? DEMO_RECENT : (data?.recent || DEMO_RECENT);

  const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: React.ElementType }> = {
    present: { color: "text-emerald-600", bg: "bg-emerald-100 dark:bg-emerald-900/30", icon: CheckCircle2 },
    absent: { color: "text-red-600", bg: "bg-red-100 dark:bg-red-900/30", icon: XCircle },
    late: { color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-900/30", icon: Clock },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">My Attendance</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Track your attendance across subjects</p>
        </div>
        {!demoMode && (
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        )}
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Classes", value: overall.total, icon: CalendarCheck, color: "text-blue-600" },
          { label: "Present", value: overall.present, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Absent", value: overall.absent, icon: XCircle, color: "text-red-600" },
          { label: "Attendance %", value: `${overall.percentage}%`, icon: TrendingUp, color: overall.percentage >= 75 ? "text-emerald-600" : "text-red-600" },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", stat.color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
                <stat.icon className={cn("h-5 w-5", stat.color)} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className={cn("text-lg font-bold", stat.color)}>{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Subject Attendance */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Subject-wise Attendance</CardTitle>
            <CardDescription>Your attendance breakdown by subject</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {subjects.map((subject: any) => (
                <div key={subject.name} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{subject.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">{subject.present}/{subject.total}</span>
                      <Badge variant={subject.percentage >= 75 ? "default" : "destructive"}>
                        {subject.percentage}%
                      </Badge>
                    </div>
                  </div>
                  <Progress value={subject.percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Attendance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Records</CardTitle>
            <CardDescription>Last few attendance entries</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recent.map((record: any, i: number) => {
                const cfg = STATUS_CONFIG[record.status] || STATUS_CONFIG.present;
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/30 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium">{record.subject}</p>
                      <p className="text-xs text-muted-foreground">{record.date}</p>
                    </div>
                    <Badge className={cn("gap-1", cfg.bg, cfg.color)}>
                      <cfg.icon className="h-3 w-3" />
                      {record.status.charAt(0).toUpperCase() + record.status.slice(1)}
                    </Badge>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StudentAttendancePage;
