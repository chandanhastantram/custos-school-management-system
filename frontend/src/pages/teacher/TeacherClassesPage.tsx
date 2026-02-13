import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  Users, BookOpen, Clock, Calendar, FileText, MoreHorizontal,
  Eye, Edit, CheckCircle2, XCircle, ChevronRight, TrendingUp,
  AlertCircle, User, GraduationCap, ClipboardList,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

// Types
interface ClassAssignment {
  id: string;
  className: string;
  section: string;
  subject: string;
  totalStudents: number;
  periodsPerWeek: number;
  syllabusProgress: number;
  attendanceToday: number;
  pendingAssignments: number;
}

interface UpcomingClass {
  id: string;
  className: string;
  subject: string;
  startTime: string;
  endTime: string;
  room: string;
  topic: string;
}

// Demo data
const DEMO_ASSIGNMENTS: ClassAssignment[] = [
  { id: "1", className: "Class 10", section: "A", subject: "Mathematics", totalStudents: 30, periodsPerWeek: 6, syllabusProgress: 72, attendanceToday: 93, pendingAssignments: 2 },
  { id: "2", className: "Class 10", section: "B", subject: "Mathematics", totalStudents: 28, periodsPerWeek: 6, syllabusProgress: 68, attendanceToday: 89, pendingAssignments: 1 },
  { id: "3", className: "Class 9", section: "A", subject: "Mathematics", totalStudents: 32, periodsPerWeek: 5, syllabusProgress: 75, attendanceToday: 97, pendingAssignments: 0 },
  { id: "4", className: "Class 9", section: "B", subject: "Mathematics", totalStudents: 30, periodsPerWeek: 5, syllabusProgress: 70, attendanceToday: 90, pendingAssignments: 3 },
];

const UPCOMING_CLASSES: UpcomingClass[] = [
  { id: "1", className: "Class 10-A", subject: "Mathematics", startTime: "10:30", endTime: "11:15", room: "Room 101", topic: "Quadratic Equations" },
  { id: "2", className: "Class 10-B", subject: "Mathematics", startTime: "11:15", endTime: "12:00", room: "Room 102", topic: "Quadratic Equations" },
  { id: "3", className: "Class 9-A", subject: "Mathematics", startTime: "13:30", endTime: "14:15", room: "Room 201", topic: "Linear Equations" },
];

const TeacherClassesPage = () => {
  const [demoMode] = useState(true);

  // Stats
  const stats = useMemo(() => ({
    totalClasses: DEMO_ASSIGNMENTS.length,
    totalStudents: DEMO_ASSIGNMENTS.reduce((sum, c) => sum + c.totalStudents, 0),
    avgAttendance: Math.round(DEMO_ASSIGNMENTS.reduce((sum, c) => sum + c.attendanceToday, 0) / DEMO_ASSIGNMENTS.length),
    pendingWork: DEMO_ASSIGNMENTS.reduce((sum, c) => sum + c.pendingAssignments, 0),
  }), []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">My Classes</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Manage your teaching assignments</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-1" /> View Schedule
          </Button>
          <Button size="sm">
            <ClipboardList className="h-4 w-4 mr-1" /> Take Attendance
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Classes Assigned", value: stats.totalClasses, icon: BookOpen, color: "text-blue-600" },
          { label: "Total Students", value: stats.totalStudents, icon: Users, color: "text-purple-600" },
          { label: "Avg Attendance", value: `${stats.avgAttendance}%`, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Pending Work", value: stats.pendingWork, icon: AlertCircle, color: "text-amber-600" },
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

      {/* Upcoming Classes */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Today's Schedule</CardTitle>
          <CardDescription>Your upcoming classes for today</CardDescription>
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
                  <span className="text-xs font-medium text-primary">{cls.startTime}</span>
                  <span className="text-[10px] text-muted-foreground">{cls.endTime}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">{cls.className}</p>
                    <Badge variant="secondary" className="text-xs">{cls.subject}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{cls.topic}</p>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                  <p>{cls.room}</p>
                </div>
                <Button variant="ghost" size="sm">
                  Start <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Class Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {DEMO_ASSIGNMENTS.map((assignment, i) => (
          <motion.div
            key={assignment.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                      <GraduationCap className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{assignment.className}-{assignment.section}</h3>
                      <p className="text-sm text-muted-foreground">{assignment.subject}</p>
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
                        <Users className="h-3.5 w-3.5 mr-2" /> View Students
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <ClipboardList className="h-3.5 w-3.5 mr-2" /> Take Attendance
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <FileText className="h-3.5 w-3.5 mr-2" /> Assignments
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4 text-center">
                  <div>
                    <p className="text-lg font-bold">{assignment.totalStudents}</p>
                    <p className="text-xs text-muted-foreground">Students</p>
                  </div>
                  <div>
                    <p className={cn("text-lg font-bold", assignment.attendanceToday >= 90 ? "text-emerald-600" : "text-amber-600")}>
                      {assignment.attendanceToday}%
                    </p>
                    <p className="text-xs text-muted-foreground">Attendance</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold">{assignment.periodsPerWeek}</p>
                    <p className="text-xs text-muted-foreground">Periods/wk</p>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Syllabus Progress</span>
                    <span className="font-medium">{assignment.syllabusProgress}%</span>
                  </div>
                  <Progress value={assignment.syllabusProgress} className="h-2" />
                </div>

                {assignment.pendingAssignments > 0 && (
                  <div className="mt-3 flex items-center gap-2 text-amber-600 text-xs">
                    <AlertCircle className="h-3.5 w-3.5" />
                    {assignment.pendingAssignments} pending assignment{assignment.pendingAssignments > 1 ? "s" : ""} to grade
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default TeacherClassesPage;
