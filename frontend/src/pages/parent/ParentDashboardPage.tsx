import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, TrendingUp, Calendar, AlertCircle, BookOpen, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { parentApi } from "@/services/parent-api";

const CHILDREN = [
  { id: "1", name: "Aisha Sharma", class: "10-A", rollNo: "10A-001", section: "A" },
  { id: "2", name: "Rahul Sharma", class: "8-B", rollNo: "8B-015", section: "B" },
];

const CHILD_DATA: Record<string, {
  attendance: number;
  avgGrade: number;
  pendingFees: number;
  subjects: { name: string; score: number; total: number; grade: string }[];
  recentAttendance: { date: string; status: string }[];
  assignments: { title: string; subject: string; status: string; due: string }[];
}> = {
  "1": {
    attendance: 92,
    avgGrade: 85,
    pendingFees: 12500,
    subjects: [
      { name: "Mathematics", score: 88, total: 100, grade: "A" },
      { name: "Science", score: 82, total: 100, grade: "B+" },
      { name: "English", score: 90, total: 100, grade: "A+" },
      { name: "Hindi", score: 78, total: 100, grade: "B" },
      { name: "Social Studies", score: 85, total: 100, grade: "A" },
    ],
    recentAttendance: [
      { date: "Mon, Feb 19", status: "present" },
      { date: "Tue, Feb 20", status: "present" },
      { date: "Wed, Feb 21", status: "absent" },
      { date: "Thu, Feb 22", status: "present" },
      { date: "Fri, Feb 23", status: "late" },
    ],
    assignments: [
      { title: "Quadratic Equations", subject: "Math", status: "pending", due: "Feb 25" },
      { title: "Lab Report", subject: "Science", status: "submitted", due: "Feb 20" },
      { title: "Essay Writing", subject: "English", status: "graded", due: "Feb 18" },
    ],
  },
  "2": {
    attendance: 88,
    avgGrade: 78,
    pendingFees: 0,
    subjects: [
      { name: "Mathematics", score: 75, total: 100, grade: "B" },
      { name: "Science", score: 80, total: 100, grade: "B+" },
      { name: "English", score: 82, total: 100, grade: "B+" },
      { name: "Hindi", score: 70, total: 100, grade: "C+" },
    ],
    recentAttendance: [
      { date: "Mon, Feb 19", status: "present" },
      { date: "Tue, Feb 20", status: "absent" },
      { date: "Wed, Feb 21", status: "present" },
      { date: "Thu, Feb 22", status: "present" },
      { date: "Fri, Feb 23", status: "present" },
    ],
    assignments: [
      { title: "Science Project", subject: "Science", status: "submitted", due: "Feb 22" },
      { title: "Grammar Sheet", subject: "English", status: "pending", due: "Feb 26" },
    ],
  },
};

const AttendanceIcon = ({ status }: { status: string }) => {
  if (status === "present") return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  if (status === "absent") return <XCircle className="h-4 w-4 text-red-600" />;
  return <Clock className="h-4 w-4 text-amber-600" />;
};

const STATUS_COLORS: Record<string, string> = {
  pending: "text-amber-600 bg-amber-50 border-amber-200",
  submitted: "text-blue-600 bg-blue-50 border-blue-200",
  graded: "text-emerald-600 bg-emerald-50 border-emerald-200",
};

const ParentDashboard = () => {
  const [selectedChild, setSelectedChild] = useState("1");
  const child = CHILDREN.find(c => c.id === selectedChild)!;
  const data = CHILD_DATA[selectedChild];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" /> Parent Dashboard
          </h1>
          <p className="text-muted-foreground text-sm">Monitor your child's academic progress</p>
        </div>
        <Select value={selectedChild} onValueChange={setSelectedChild}>
          <SelectTrigger className="w-56">
            <SelectValue placeholder="Select child" />
          </SelectTrigger>
          <SelectContent>
            {CHILDREN.map(c => (
              <SelectItem key={c.id} value={c.id}>{c.name} – Class {c.class}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <motion.div key={selectedChild} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
        {/* Child Card */}
        <Card className="border-2 border-primary/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <Avatar className="h-14 w-14">
                <AvatarFallback className="text-lg bg-primary/10 text-primary">
                  {child.name.split(" ").map(n => n[0]).join("")}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-xl font-bold">{child.name}</h2>
                <p className="text-muted-foreground text-sm">Class {child.class} • Roll No: {child.rollNo}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Attendance</p>
              <p className={cn("text-2xl font-bold", data.attendance >= 85 ? "text-emerald-600" : "text-red-600")}>
                {data.attendance}%
              </p>
              <Progress value={data.attendance} className="h-1.5 mt-2" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Avg Grade</p>
              <p className="text-2xl font-bold text-primary">{data.avgGrade}%</p>
              <Progress value={data.avgGrade} className="h-1.5 mt-2" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Pending Fees</p>
              <p className={cn("text-2xl font-bold", data.pendingFees > 0 ? "text-red-600" : "text-emerald-600")}>
                {data.pendingFees > 0 ? `₹${data.pendingFees.toLocaleString()}` : "Clear"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Subjects</p>
              <p className="text-2xl font-bold">{data.subjects.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="academics" className="space-y-4">
          <TabsList>
            <TabsTrigger value="academics">Academics</TabsTrigger>
            <TabsTrigger value="attendance">Attendance</TabsTrigger>
            <TabsTrigger value="assignments">Assignments</TabsTrigger>
          </TabsList>

          <TabsContent value="academics">
            <Card>
              <CardHeader>
                <CardTitle>Subject Performance</CardTitle>
                <CardDescription>Latest marks across all subjects</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.subjects.map(sub => (
                    <div key={sub.name} className="space-y-1.5">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{sub.name}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-muted-foreground">{sub.score}/{sub.total}</span>
                          <Badge variant="outline" className={cn(
                            sub.score >= 85 ? "border-emerald-300 text-emerald-600 bg-emerald-50" :
                            sub.score >= 70 ? "border-blue-300 text-blue-600 bg-blue-50" :
                            "border-red-300 text-red-600 bg-red-50"
                          )}>
                            {sub.grade}
                          </Badge>
                        </div>
                      </div>
                      <Progress value={(sub.score / sub.total) * 100} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="attendance">
            <Card>
              <CardHeader>
                <CardTitle>Recent Attendance</CardTitle>
                <CardDescription>Last 5 school days</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {data.recentAttendance.map((r, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="text-sm font-medium">{r.date}</span>
                      <div className="flex items-center gap-2">
                        <AttendanceIcon status={r.status} />
                        <span className={cn("text-sm capitalize",
                          r.status === "present" ? "text-emerald-600" :
                          r.status === "absent" ? "text-red-600" : "text-amber-600"
                        )}>{r.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-muted/50 rounded-lg text-sm text-center">
                  Overall Attendance: <span className="font-bold text-lg">{data.attendance}%</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="assignments">
            <Card>
              <CardHeader>
                <CardTitle>Assignments</CardTitle>
                <CardDescription>Pending and recent submissions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.assignments.map((a, i) => (
                    <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{a.title}</p>
                        <p className="text-xs text-muted-foreground">{a.subject} • Due: {a.due}</p>
                      </div>
                      <Badge variant="outline" className={STATUS_COLORS[a.status]}>{a.status}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ParentDashboard;
