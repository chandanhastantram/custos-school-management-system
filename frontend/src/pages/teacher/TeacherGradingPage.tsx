import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  FileText, CheckCircle2, XCircle, Clock, MoreHorizontal, Eye,
  Edit, Download, Search, Filter, Users, BookOpen, Award,
  TrendingUp, AlertCircle, ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
import {
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// Types
type AssignmentStatus = "pending" | "submitted" | "graded" | "late";

interface Assignment {
  id: string;
  title: string;
  className: string;
  subject: string;
  dueDate: string;
  totalSubmissions: number;
  gradedCount: number;
  totalStudents: number;
  avgScore?: number;
}

interface Submission {
  id: string;
  studentName: string;
  rollNo: string;
  submittedAt: string;
  status: AssignmentStatus;
  score?: number;
  maxScore: number;
  feedback?: string;
}

// Demo data
const DEMO_ASSIGNMENTS: Assignment[] = [
  { id: "1", title: "Quadratic Equations Practice", className: "Class 10-A", subject: "Mathematics", dueDate: "2024-11-15", totalSubmissions: 28, gradedCount: 28, totalStudents: 30, avgScore: 78 },
  { id: "2", title: "Linear Equations Worksheet", className: "Class 9-A", subject: "Mathematics", dueDate: "2024-11-18", totalSubmissions: 30, gradedCount: 25, totalStudents: 32 },
  { id: "3", title: "Geometry Problems Set 1", className: "Class 10-B", subject: "Mathematics", dueDate: "2024-11-20", totalSubmissions: 15, gradedCount: 0, totalStudents: 28 },
  { id: "4", title: "Algebra Quiz Prep", className: "Class 9-B", subject: "Mathematics", dueDate: "2024-11-22", totalSubmissions: 5, gradedCount: 0, totalStudents: 30 },
];

const DEMO_SUBMISSIONS: Submission[] = [
  { id: "s1", studentName: "Aisha Sharma", rollNo: "10A01", submittedAt: "2024-11-14T09:30:00", status: "graded", score: 92, maxScore: 100, feedback: "Excellent work!" },
  { id: "s2", studentName: "Rahul Verma", rollNo: "10A02", submittedAt: "2024-11-14T10:15:00", status: "graded", score: 85, maxScore: 100, feedback: "Good effort" },
  { id: "s3", studentName: "Priya Patel", rollNo: "10A03", submittedAt: "2024-11-15T11:00:00", status: "submitted", maxScore: 100 },
  { id: "s4", studentName: "Vikram Singh", rollNo: "10A04", submittedAt: "2024-11-16T08:30:00", status: "late", maxScore: 100 },
  { id: "s5", studentName: "Nisha Gupta", rollNo: "10A05", submittedAt: "", status: "pending", maxScore: 100 },
  { id: "s6", studentName: "Arjun Kumar", rollNo: "10A06", submittedAt: "2024-11-14T14:00:00", status: "graded", score: 78, maxScore: 100 },
];

const STATUS_CONFIG: Record<AssignmentStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: "Pending", color: "text-gray-600", bgColor: "bg-gray-100 dark:bg-gray-800" },
  submitted: { label: "Submitted", color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" },
  graded: { label: "Graded", color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-900/30" },
  late: { label: "Late", color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-900/30" },
};

const TeacherGradingPage = () => {
  const [tab, setTab] = useState("assignments");
  const [search, setSearch] = useState("");
  const [selectedAssignment, setSelectedAssignment] = useState<string | null>(null);
  const [demoMode] = useState(true);

  // Stats
  const stats = useMemo(() => ({
    totalAssignments: DEMO_ASSIGNMENTS.length,
    pendingGrading: DEMO_ASSIGNMENTS.reduce((sum, a) => sum + (a.totalSubmissions - a.gradedCount), 0),
    avgScore: 82,
    completionRate: 85,
  }), []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Grading</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Grade assignments and track student performance</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export Grades
          </Button>
          <Button size="sm">
            <FileText className="h-4 w-4 mr-1" /> Create Assignment
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Assignments", value: stats.totalAssignments, icon: FileText, color: "text-blue-600" },
          { label: "Pending Grading", value: stats.pendingGrading, icon: Clock, color: "text-amber-600" },
          { label: "Avg Score", value: `${stats.avgScore}%`, icon: TrendingUp, color: "text-emerald-600" },
          { label: "Completion Rate", value: `${stats.completionRate}%`, icon: CheckCircle2, color: "text-purple-600" },
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

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="assignments">Assignments</TabsTrigger>
            <TabsTrigger value="submissions">Submissions</TabsTrigger>
          </TabsList>
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Assignments Tab */}
        <TabsContent value="assignments" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {DEMO_ASSIGNMENTS.map((assignment, i) => {
              const gradingProgress = assignment.totalSubmissions > 0 
                ? (assignment.gradedCount / assignment.totalSubmissions) * 100 
                : 0;
              const submissionRate = (assignment.totalSubmissions / assignment.totalStudents) * 100;
              
              return (
                <motion.div
                  key={assignment.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-sm">{assignment.title}</h3>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">{assignment.className}</Badge>
                            <span className="text-xs text-muted-foreground">Due: {format(new Date(assignment.dueDate), "MMM d")}</span>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Eye className="h-3.5 w-3.5 mr-2" /> View Submissions
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Edit className="h-3.5 w-3.5 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Download className="h-3.5 w-3.5 mr-2" /> Export Grades
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>

                      <div className="grid grid-cols-3 gap-2 mt-4 text-center text-xs">
                        <div className="p-2 rounded-lg bg-muted/50">
                          <p className="font-bold">{assignment.totalSubmissions}/{assignment.totalStudents}</p>
                          <p className="text-muted-foreground">Submitted</p>
                        </div>
                        <div className="p-2 rounded-lg bg-muted/50">
                          <p className="font-bold">{assignment.gradedCount}</p>
                          <p className="text-muted-foreground">Graded</p>
                        </div>
                        <div className="p-2 rounded-lg bg-muted/50">
                          <p className="font-bold">{assignment.avgScore ? `${assignment.avgScore}%` : "-"}</p>
                          <p className="text-muted-foreground">Avg Score</p>
                        </div>
                      </div>

                      <div className="mt-3 space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Grading Progress</span>
                          <span>{Math.round(gradingProgress)}%</span>
                        </div>
                        <Progress value={gradingProgress} className="h-1.5" />
                      </div>

                      {assignment.gradedCount < assignment.totalSubmissions && (
                        <Button variant="outline" size="sm" className="w-full mt-3">
                          Grade ({assignment.totalSubmissions - assignment.gradedCount} pending)
                          <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </TabsContent>

        {/* Submissions Tab */}
        <TabsContent value="submissions" className="space-y-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Student</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead>Feedback</TableHead>
                  <TableHead className="w-[80px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {DEMO_SUBMISSIONS.map((sub, i) => (
                  <motion.tr
                    key={sub.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-border hover:bg-muted/30 transition-colors"
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-7 w-7">
                          <AvatarFallback className="bg-primary/10 text-primary text-xs">
                            {sub.studentName.split(" ").map(n => n[0]).join("")}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-sm">{sub.studentName}</p>
                          <p className="text-xs text-muted-foreground">{sub.rollNo}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {sub.submittedAt ? format(new Date(sub.submittedAt), "MMM d, h:mm a") : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge className={cn("gap-1", STATUS_CONFIG[sub.status].bgColor, STATUS_CONFIG[sub.status].color)}>
                        {STATUS_CONFIG[sub.status].label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {sub.score !== undefined ? (
                        <span className={cn("font-medium", sub.score >= 80 ? "text-emerald-600" : sub.score >= 60 ? "text-blue-600" : "text-amber-600")}>
                          {sub.score}/{sub.maxScore}
                        </span>
                      ) : "-"}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-[150px] truncate">
                      {sub.feedback || "-"}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        {sub.status === "graded" ? "View" : "Grade"}
                      </Button>
                    </TableCell>
                  </motion.tr>
                ))}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TeacherGradingPage;
