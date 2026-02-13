import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format, addDays } from "date-fns";
import {
  BookOpen, Calendar, Clock, FileText, Award, TrendingUp,
  CheckCircle2, AlertCircle, ChevronRight, Bell, User,
  GraduationCap, BarChart3, Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// Types
interface Course {
  id: string;
  name: string;
  teacher: string;
  progress: number;
  nextClass: string;
  grade?: string;
}

interface UpcomingClass {
  id: string;
  subject: string;
  teacher: string;
  time: string;
  room: string;
  topic: string;
}

interface Assignment {
  id: string;
  title: string;
  subject: string;
  dueDate: string;
  status: "pending" | "submitted" | "graded";
  score?: number;
}

interface Result {
  examName: string;
  totalMarks: number;
  obtainedMarks: number;
  percentage: number;
  grade: string;
  rank: number;
}

// Demo data
const DEMO_COURSES: Course[] = [
  { id: "1", name: "Mathematics", teacher: "Mr. Sharma", progress: 72, nextClass: "10:30 AM", grade: "A" },
  { id: "2", name: "Science", teacher: "Mr. Patel", progress: 68, nextClass: "11:15 AM", grade: "A-" },
  { id: "3", name: "English", teacher: "Mrs. Verma", progress: 75, nextClass: "Tomorrow", grade: "B+" },
  { id: "4", name: "Hindi", teacher: "Mrs. Singh", progress: 80, nextClass: "Tomorrow", grade: "A" },
  { id: "5", name: "Social Science", teacher: "Mr. Gupta", progress: 65, nextClass: "Wed", grade: "B" },
  { id: "6", name: "Computer Science", teacher: "Mr. Kumar", progress: 85, nextClass: "Thu", grade: "A+" },
];

const UPCOMING_CLASSES: UpcomingClass[] = [
  { id: "1", subject: "Mathematics", teacher: "Mr. Sharma", time: "10:30 AM", room: "101", topic: "Quadratic Equations" },
  { id: "2", subject: "Science", teacher: "Mr. Patel", time: "11:15 AM", room: "Lab 1", topic: "Chemical Reactions" },
  { id: "3", subject: "English", teacher: "Mrs. Verma", time: "12:00 PM", room: "101", topic: "Shakespeare's Sonnets" },
];

const PENDING_ASSIGNMENTS: Assignment[] = [
  { id: "1", title: "Quadratic Equations Practice", subject: "Mathematics", dueDate: "2024-11-18", status: "pending" },
  { id: "2", title: "Chemistry Lab Report", subject: "Science", dueDate: "2024-11-20", status: "pending" },
  { id: "3", title: "Essay on Climate Change", subject: "English", dueDate: "2024-11-22", status: "pending" },
];

const RECENT_RESULTS: Result = {
  examName: "Mid-Term Examination",
  totalMarks: 600,
  obtainedMarks: 534,
  percentage: 89,
  grade: "A",
  rank: 5,
};

const GRADE_COLORS: Record<string, string> = {
  "A+": "text-emerald-600",
  "A": "text-green-600",
  "A-": "text-green-500",
  "B+": "text-blue-600",
  "B": "text-blue-500",
  "C": "text-amber-600",
  "D": "text-orange-600",
};

const StudentDashboardPage = () => {
  const [demoMode] = useState(true);

  const stats = useMemo(() => ({
    attendanceRate: 94,
    avgGrade: "A-",
    pendingAssignments: PENDING_ASSIGNMENTS.length,
    classRank: RECENT_RESULTS.rank,
  }), []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarFallback className="bg-primary/10 text-primary text-lg">AS</AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold">Welcome, Aisha!</h1>
              <p className="text-muted-foreground text-sm">Class 10-A · Roll No: 01</p>
            </div>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800 ml-2">
                Demo
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Bell className="h-4 w-4 mr-1" /> Notifications
          </Button>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-1" /> My Schedule
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Attendance", value: `${stats.attendanceRate}%`, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Avg Grade", value: stats.avgGrade, icon: Award, color: "text-purple-600" },
          { label: "Pending Work", value: stats.pendingAssignments, icon: FileText, color: "text-amber-600" },
          { label: "Class Rank", value: `#${stats.classRank}`, icon: TrendingUp, color: "text-blue-600" },
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
        {/* Today's Classes */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Today's Classes</CardTitle>
            <CardDescription>Your schedule for today</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {UPCOMING_CLASSES.map((cls, i) => (
                <motion.div
                  key={cls.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-4 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                >
                  <div className="h-12 w-12 rounded-lg bg-primary/10 flex flex-col items-center justify-center">
                    <Clock className="h-4 w-4 text-primary" />
                    <span className="text-[10px] font-medium text-primary">{cls.time}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{cls.subject}</p>
                      <Badge variant="secondary" className="text-xs">{cls.room}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{cls.topic} · {cls.teacher}</p>
                  </div>
                  <Button variant="ghost" size="sm">
                    Join <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Result */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Recent Result</CardTitle>
            <CardDescription>{RECENT_RESULTS.examName}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30 mb-3">
                <span className="text-3xl font-bold text-emerald-600">{RECENT_RESULTS.grade}</span>
              </div>
              <p className="text-2xl font-bold">{RECENT_RESULTS.percentage}%</p>
              <p className="text-sm text-muted-foreground">{RECENT_RESULTS.obtainedMarks}/{RECENT_RESULTS.totalMarks} marks</p>
              <Badge variant="secondary" className="mt-2">Rank #{RECENT_RESULTS.rank} in class</Badge>
            </div>
            <Button variant="outline" className="w-full mt-4" size="sm">
              <Download className="h-4 w-4 mr-1" /> Download Report Card
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Pending Assignments */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Pending Assignments</CardTitle>
              <CardDescription>Complete before the due date</CardDescription>
            </div>
            <Button variant="outline" size="sm">View All</Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-3">
            {PENDING_ASSIGNMENTS.map((assignment, i) => (
              <motion.div
                key={assignment.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-4 rounded-lg border bg-card hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <Badge variant="secondary" className="text-xs">{assignment.subject}</Badge>
                  <span className="text-xs text-muted-foreground">
                    Due: {format(new Date(assignment.dueDate), "MMM d")}
                  </span>
                </div>
                <p className="font-medium text-sm mt-2">{assignment.title}</p>
                <Button variant="outline" size="sm" className="w-full mt-3">
                  Start Assignment
                </Button>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* My Courses */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">My Courses</CardTitle>
          <CardDescription>Track your progress across all subjects</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {DEMO_COURSES.map((course, i) => (
              <motion.div
                key={course.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className="p-4 rounded-lg border bg-card hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                  <span className={cn("text-lg font-bold", GRADE_COLORS[course.grade || ""] || "text-muted-foreground")}>
                    {course.grade}
                  </span>
                </div>
                <div className="mt-3">
                  <p className="font-medium">{course.name}</p>
                  <p className="text-xs text-muted-foreground">{course.teacher}</p>
                </div>
                <div className="mt-3 space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Progress</span>
                    <span>{course.progress}%</span>
                  </div>
                  <Progress value={course.progress} className="h-1.5" />
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Next: {course.nextClass}
                </p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentDashboardPage;
