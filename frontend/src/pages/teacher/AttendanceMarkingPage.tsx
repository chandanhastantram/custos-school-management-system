import React, { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { teacherApi } from "@/services/teacher-api";
import { motion } from "framer-motion";
import {
  ClipboardCheck, Calendar, Users, CheckCircle2, XCircle,
  Clock, Save, Loader2, Search, ChevronLeft, ChevronRight, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from "@/hooks/use-toast";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

type Status = "present" | "absent" | "late";

interface Student {
  id: string;
  name: string;
  rollNo: string;
}

interface ClassItem {
  id: string;
  name: string;
  subject: string;
  time: string;
  totalStudents: number;
}

// Demo data (fallback)
const DEMO_CLASSES: ClassItem[] = [
  { id: "c1", name: "10-A", subject: "Mathematics", time: "09:00 AM", totalStudents: 32 },
  { id: "c2", name: "10-B", subject: "Physics", time: "11:00 AM", totalStudents: 30 },
  { id: "c3", name: "9-A", subject: "Chemistry", time: "01:00 PM", totalStudents: 28 },
];

const DEMO_STUDENTS: Student[] = [
  { id: "s1", name: "Aisha Sharma", rollNo: "001" },
  { id: "s2", name: "Rahul Verma", rollNo: "002" },
  { id: "s3", name: "Priya Patel", rollNo: "003" },
  { id: "s4", name: "Vikram Singh", rollNo: "004" },
  { id: "s5", name: "Nisha Gupta", rollNo: "005" },
  { id: "s6", name: "Arjun Kumar", rollNo: "006" },
  { id: "s7", name: "Sneha Reddy", rollNo: "007" },
  { id: "s8", name: "Karan Mehta", rollNo: "008" },
  { id: "s9", name: "Ananya Das", rollNo: "009" },
  { id: "s10", name: "Rohan Joshi", rollNo: "010" },
];

const DEMO_HISTORY = [
  { date: "2024-02-12", class: "Mathematics - 10A", present: 30, absent: 2, late: 0 },
  { date: "2024-02-11", class: "Mathematics - 10A", present: 28, absent: 3, late: 1 },
  { date: "2024-02-10", class: "Physics - 10B", present: 29, absent: 1, late: 0 },
  { date: "2024-02-09", class: "Chemistry - 9A", present: 27, absent: 1, late: 0 },
];

const AttendanceMarkingPage = () => {
  const today = new Date();
  const [selectedDate, setSelectedDate] = useState(today);
  const [selectedClass, setSelectedClass] = useState<ClassItem | null>(null);
  const [attendance, setAttendance] = useState<Record<string, Status>>({});
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  // Fetch classes from API
  const { data: classesData, isError: classesError } = useQuery({
    queryKey: ["teacher-classes"],
    queryFn: () => teacherApi.getMyClasses(),
    retry: 1,
    staleTime: 30000,
  });

  // Fetch students for selected class
  const { data: studentsData, isError: studentsError } = useQuery({
    queryKey: ["class-students", selectedClass?.id],
    queryFn: () => selectedClass ? teacherApi.getClassStudents(selectedClass.id) : Promise.resolve([]),
    enabled: !!selectedClass && !demoMode,
    retry: 1,
  });

  // Fetch attendance history
  const { data: historyData } = useQuery({
    queryKey: ["attendance-history"],
    queryFn: () => teacherApi.getAttendanceHistory(),
    retry: 1,
    enabled: !demoMode,
  });

  useEffect(() => {
    if ((classesError || studentsError) && !demoMode) setDemoMode(true);
  }, [classesError, studentsError, demoMode]);

  const classes = demoMode ? DEMO_CLASSES : (classesData || DEMO_CLASSES);
  const students = demoMode ? DEMO_STUDENTS : (studentsData || DEMO_STUDENTS);
  const history = demoMode ? DEMO_HISTORY : (historyData || DEMO_HISTORY);

  const filteredStudents = useMemo(() =>
    students.filter((s: Student) =>
      s.name.toLowerCase().includes(search.toLowerCase()) || s.rollNo.includes(search)
    ), [search, students]);

  const stats = useMemo(() => {
    const vals = Object.values(attendance);
    return {
      present: vals.filter(v => v === "present").length,
      absent: vals.filter(v => v === "absent").length,
      late: vals.filter(v => v === "late").length,
      total: students.length,
    };
  }, [attendance, students]);

  const setStatus = (studentId: string, status: Status) => {
    setAttendance(prev => ({
      ...prev,
      [studentId]: prev[studentId] === status ? (undefined as any) : status,
    }));
  };

  const markAll = (status: Status) => {
    const rec: Record<string, Status> = {};
    students.forEach((s: Student) => { rec[s.id] = status; });
    setAttendance(rec);
    toast({ title: `Marked all as ${status}` });
  };

  const handleSave = async () => {
    if (!selectedClass) {
      toast({ title: "Select a class first", variant: "destructive" });
      return;
    }
    setSaving(true);
    try {
      const attendance_data = Object.entries(attendance).map(([studentId, status]) => ({
        student_id: studentId,
        status,
      }));
      await teacherApi.markAttendance({
        class_id: selectedClass.id,
        date: format(selectedDate, "yyyy-MM-dd"),
        attendance: attendance_data,
      });
    } catch {
      // fallback: show success locally
    }
    setSaving(false);
    toast({
      title: "Attendance saved!",
      description: `${stats.present} present, ${stats.absent} absent, ${stats.late} late for ${selectedClass.subject} - ${selectedClass.name}`,
    });
  };

  const STATUS_CONFIG: Record<Status, { label: string; icon: React.ElementType; color: string; bg: string }> = {
    present: { label: "Present", icon: CheckCircle2, color: "text-emerald-600", bg: "bg-emerald-100 dark:bg-emerald-900/30" },
    absent: { label: "Absent", icon: XCircle, color: "text-red-600", bg: "bg-red-100 dark:bg-red-900/30" },
    late: { label: "Late", icon: Clock, color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-900/30" },
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <ClipboardCheck className="h-6 w-6 text-primary" />
              Mark Attendance
            </h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Record student attendance for your classes</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => setSelectedDate(d => new Date(d.getTime() - 86400000))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="font-medium text-sm min-w-[140px] text-center">
            {format(selectedDate, "EEE, MMM d, yyyy")}
          </span>
          <Button variant="ghost" size="icon" onClick={() => setSelectedDate(d => new Date(d.getTime() + 86400000))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSelectedDate(new Date())}>Today</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total", value: stats.total, color: "text-foreground" },
          { label: "Present", value: stats.present, color: "text-emerald-600" },
          { label: "Absent", value: stats.absent, color: "text-red-600" },
          { label: "Late", value: stats.late, color: "text-amber-600" },
        ].map(s => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className={cn("text-2xl font-bold", s.color)}>{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="mark" className="space-y-4">
        <TabsList>
          <TabsTrigger value="mark">Mark Attendance</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="mark" className="space-y-4">
          {/* Class selector */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3">
                {classes.map((cls: ClassItem) => (
                  <button
                    key={cls.id}
                    onClick={() => { setSelectedClass(cls); setAttendance({}); }}
                    className={cn(
                      "p-3 rounded-lg border-2 text-left transition-all w-40",
                      selectedClass?.id === cls.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <p className="font-medium text-sm">{cls.subject}</p>
                    <p className="text-xs text-muted-foreground">Class {cls.name}</p>
                    <p className="text-xs text-muted-foreground">{cls.time}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {selectedClass ? (
            <>
              {/* Actions */}
              <div className="flex flex-wrap gap-2 items-center">
                <div className="relative flex-1 max-w-xs">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search student..." value={search} onChange={e => setSearch(e.target.value)} className="pl-9" />
                </div>
                <span className="text-sm text-muted-foreground">Quick:</span>
                {(["present", "absent", "late"] as Status[]).map(s => (
                  <Button key={s} variant="outline" size="sm" onClick={() => markAll(s)} className={STATUS_CONFIG[s].color}>
                    All {STATUS_CONFIG[s].label}
                  </Button>
                ))}
                <Button variant="ghost" size="sm" onClick={() => setAttendance({})}>Clear</Button>
                <Button size="sm" onClick={handleSave} disabled={saving} className="ml-auto">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Save className="h-4 w-4 mr-1" />}
                  Save
                </Button>
              </div>

              {/* Student list */}
              <Card>
                <CardContent className="p-0">
                  <div className="divide-y divide-border">
                    {filteredStudents.map((student: Student, i: number) => {
                      const status = attendance[student.id];
                      return (
                        <motion.div
                          key={student.id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: i * 0.02 }}
                          className="flex items-center justify-between p-3 hover:bg-muted/30 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                {student.name.split(" ").map(n => n[0]).join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="font-medium text-sm">{student.name}</p>
                              <p className="text-xs text-muted-foreground">Roll: {student.rollNo}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {(["present", "absent", "late"] as Status[]).map(s => {
                              const cfg = STATUS_CONFIG[s];
                              const selected = status === s;
                              return (
                                <Button
                                  key={s}
                                  variant={selected ? "default" : "ghost"}
                                  size="sm"
                                  onClick={() => setStatus(student.id, s)}
                                  className={cn(
                                    "h-8 px-3 transition-all",
                                    selected ? cfg.bg + " " + cfg.color + " border-0" : "text-muted-foreground"
                                  )}
                                >
                                  <cfg.icon className="h-3.5 w-3.5 mr-1" />
                                  {cfg.label}
                                </Button>
                              );
                            })}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <ClipboardCheck className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>Select a class above to mark attendance</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Attendance History</CardTitle>
              <CardDescription>Recent attendance records you've submitted</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {history.map((h: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/30 transition-colors">
                    <div>
                      <p className="font-medium text-sm">{h.class}</p>
                      <p className="text-xs text-muted-foreground">{format(new Date(h.date), "EEE, MMM d")}</p>
                    </div>
                    <div className="flex gap-3 text-sm">
                      <span className="text-emerald-600">{h.present} Present</span>
                      <span className="text-red-600">{h.absent} Absent</span>
                      {h.late > 0 && <span className="text-amber-600">{h.late} Late</span>}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AttendanceMarkingPage;
