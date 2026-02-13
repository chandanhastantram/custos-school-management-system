import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Users, GraduationCap, DollarSign, TrendingUp, TrendingDown,
  Calendar, Clock, BarChart3, PieChart, ArrowUpRight, ArrowDownRight,
  Activity, BookOpen, CheckCircle2, AlertCircle, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import AIInsights from "@/components/ai/AIInsights";
import { cn } from "@/lib/utils";

// Demo Data
const MONTHLY_ATTENDANCE = [
  { month: "Apr", rate: 94 },
  { month: "May", rate: 92 },
  { month: "Jun", rate: 88 },
  { month: "Jul", rate: 91 },
  { month: "Aug", rate: 93 },
  { month: "Sep", rate: 95 },
  { month: "Oct", rate: 94 },
  { month: "Nov", rate: 96 },
  { month: "Dec", rate: 89 },
  { month: "Jan", rate: 97 },
  { month: "Feb", rate: 95 },
];

const CLASS_PERFORMANCE = [
  { class: "Class 10", avg: 82, students: 58, passRate: 98 },
  { class: "Class 9", avg: 78, students: 91, passRate: 95 },
  { class: "Class 8", avg: 75, students: 68, passRate: 94 },
  { class: "Class 7", avg: 80, students: 34, passRate: 97 },
];

const FEE_COLLECTION = [
  { class: "Class 10", collected: 1215000, total: 1350000 },
  { class: "Class 9", collected: 1075200, total: 1344000 },
  { class: "Class 8", collected: 882000, total: 1008000 },
  { class: "Class 7", collected: 510000, total: 612000 },
];

const TOP_PERFORMERS = [
  { name: "Aisha Sharma", class: "10-A", score: 94.5, trend: "up" },
  { name: "Rahul Verma", class: "10-A", score: 89.0, trend: "up" },
  { name: "Priya Patel", class: "9-A", score: 92.3, trend: "down" },
  { name: "Vikram Singh", class: "10-B", score: 88.5, trend: "up" },
  { name: "Nisha Gupta", class: "9-A", score: 87.2, trend: "stable" },
];

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    notation: "compact",
  }).format(amount);
};

const AnalyticsPage = () => {
  const [period, setPeriod] = useState("this_month");
  const [demoMode] = useState(true);

  // Stats
  const stats = useMemo(() => {
    const totalCollected = FEE_COLLECTION.reduce((sum, c) => sum + c.collected, 0);
    const totalFees = FEE_COLLECTION.reduce((sum, c) => sum + c.total, 0);
    return {
      totalStudents: CLASS_PERFORMANCE.reduce((sum, c) => sum + c.students, 0),
      avgAttendance: 94.2,
      avgPerformance: 78.5,
      feeCollection: (totalCollected / totalFees) * 100,
      totalCollected,
      totalFees,
    };
  }, []);

  const StatCard = ({ 
    title, value, subtitle, icon: Icon, trend, trendValue, color 
  }: { 
    title: string; 
    value: string | number; 
    subtitle?: string;
    icon: React.ElementType; 
    trend?: "up" | "down";
    trendValue?: string;
    color: string;
  }) => (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className={cn("text-2xl font-bold", color)}>{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
            {trend && trendValue && (
              <div className={cn("flex items-center gap-1 text-xs", trend === "up" ? "text-emerald-600" : "text-red-500")}>
                {trend === "up" ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {trendValue}
              </div>
            )}
          </div>
          <div className={cn("h-12 w-12 rounded-xl flex items-center justify-center", color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
            <Icon className={cn("h-6 w-6", color)} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Analytics</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">School performance insights and metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="this_week">This Week</SelectItem>
              <SelectItem value="this_month">This Month</SelectItem>
              <SelectItem value="this_quarter">This Quarter</SelectItem>
              <SelectItem value="this_year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Students"
          value={stats.totalStudents}
          subtitle="Active enrollment"
          icon={Users}
          trend="up"
          trendValue="+12 this month"
          color="text-blue-600"
        />
        <StatCard
          title="Avg Attendance"
          value={`${stats.avgAttendance}%`}
          subtitle="This month"
          icon={CheckCircle2}
          trend="up"
          trendValue="+2.3% vs last month"
          color="text-emerald-600"
        />
        <StatCard
          title="Academic Avg"
          value={`${stats.avgPerformance}%`}
          subtitle="Mid-term results"
          icon={GraduationCap}
          trend="up"
          trendValue="+5.2% vs last exam"
          color="text-purple-600"
        />
        <StatCard
          title="Fee Collection"
          value={`${stats.feeCollection.toFixed(1)}%`}
          subtitle={formatCurrency(stats.totalCollected)}
          icon={DollarSign}
          color="text-amber-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Attendance Trend */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Attendance Trend</CardTitle>
              <Badge variant="secondary" className="text-xs">Monthly</Badge>
            </div>
            <CardDescription>Average attendance rate over the year</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-1 h-40">
              {MONTHLY_ATTENDANCE.map((item, i) => (
                <div key={item.month} className="flex-1 flex flex-col items-center gap-1">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${item.rate}%` }}
                    transition={{ delay: i * 0.05, duration: 0.3 }}
                    className={cn(
                      "w-full rounded-t-sm",
                      item.rate >= 95 ? "bg-emerald-500" : 
                      item.rate >= 90 ? "bg-blue-500" : 
                      item.rate >= 85 ? "bg-amber-500" : "bg-red-500"
                    )}
                    style={{ maxHeight: `${item.rate}%` }}
                  />
                  <span className="text-[10px] text-muted-foreground">{item.month}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Class Performance */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Class Performance</CardTitle>
            <CardDescription>Academic averages by class</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {CLASS_PERFORMANCE.map((item) => (
                <div key={item.class} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{item.class}</span>
                      <span className="text-xs text-muted-foreground">({item.students} students)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "font-medium",
                        item.avg >= 80 ? "text-emerald-600" : 
                        item.avg >= 70 ? "text-blue-600" : "text-amber-600"
                      )}>
                        {item.avg}%
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {item.passRate}% pass
                      </Badge>
                    </div>
                  </div>
                  <Progress value={item.avg} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Fee Collection by Class */}
        <Card className="md:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Fee Collection Status</CardTitle>
            <CardDescription>Collection progress by class</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {FEE_COLLECTION.map((item) => {
                const percentage = (item.collected / item.total) * 100;
                return (
                  <div key={item.class} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{item.class}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">
                          {formatCurrency(item.collected)} / {formatCurrency(item.total)}
                        </span>
                        <Badge variant={percentage >= 80 ? "default" : percentage >= 60 ? "secondary" : "destructive"}>
                          {percentage.toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Top Performers</CardTitle>
            <CardDescription>Mid-term examination</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {TOP_PERFORMERS.map((student, i) => (
                <div key={student.name} className="flex items-center gap-3">
                  <div className={cn(
                    "h-7 w-7 rounded-full flex items-center justify-center font-bold text-xs",
                    i === 0 ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30" :
                    i === 1 ? "bg-gray-100 text-gray-700 dark:bg-gray-800" :
                    i === 2 ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30" :
                    "bg-muted text-muted-foreground"
                  )}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{student.name}</p>
                    <p className="text-xs text-muted-foreground">{student.class}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-sm font-medium">{student.score}%</span>
                    {student.trend === "up" && <TrendingUp className="h-3 w-3 text-emerald-500" />}
                    {student.trend === "down" && <TrendingDown className="h-3 w-3 text-red-500" />}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Classes Today", value: 24, icon: Calendar, color: "text-blue-600" },
          { label: "Teachers Present", value: 18, icon: Users, color: "text-emerald-600" },
          { label: "Pending Fees", value: "₹12.4L", icon: AlertCircle, color: "text-red-600" },
          { label: "Active Events", value: 3, icon: Activity, color: "text-purple-600" },
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

      {/* AI Insights Section */}
      <AIInsights showRecommendations={false} />
    </div>
  );
};

export default AnalyticsPage;
