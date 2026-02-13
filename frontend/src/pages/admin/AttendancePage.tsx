import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isWeekend } from "date-fns";
import {
  Calendar, Users, Check, X, Clock, AlertCircle, Loader2,
  ChevronLeft, ChevronRight, CheckCircle2, XCircle, MinusCircle,
  RefreshCw, Download, Filter, Search,
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
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Tooltip, TooltipContent, TooltipTrigger, TooltipProvider,
} from "@/components/ui/tooltip";
import apiClient, { ApiError } from "@/lib/api-client";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// Types
type AttendanceStatus = "present" | "absent" | "late" | "half_day" | "excused";

interface Student {
  id: string;
  name: string;
  rollNumber: string;
  status?: AttendanceStatus;
}

interface ClassOption {
  id: string;
  name: string;
  sections: { id: string; name: string }[];
}

interface AttendanceRecord {
  id: string;
  student_id: string;
  status: AttendanceStatus;
  check_in_time?: string;
  remarks?: string;
}

interface DailyReport {
  attendance_date: string;
  class_id: string;
  class_name: string;
  total_students: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  not_marked_count: number;
}

// Demo data
const DEMO_CLASSES: ClassOption[] = [
  { id: "c1", name: "Class 10-A", sections: [{ id: "s1", name: "Section A" }, { id: "s2", name: "Section B" }] },
  { id: "c2", name: "Class 10-B", sections: [{ id: "s3", name: "Section A" }] },
  { id: "c3", name: "Class 9-A", sections: [{ id: "s4", name: "Section A" }, { id: "s5", name: "Section B" }] },
  { id: "c4", name: "Class 9-B", sections: [] },
];

const DEMO_STUDENTS: Student[] = [
  { id: "st1", name: "Aisha Sharma", rollNumber: "001" },
  { id: "st2", name: "Rahul Verma", rollNumber: "002" },
  { id: "st3", name: "Priya Patel", rollNumber: "003" },
  { id: "st4", name: "Vikram Singh", rollNumber: "004" },
  { id: "st5", name: "Nisha Gupta", rollNumber: "005" },
  { id: "st6", name: "Arjun Kumar", rollNumber: "006" },
  { id: "st7", name: "Sneha Reddy", rollNumber: "007" },
  { id: "st8", name: "Karan Mehta", rollNumber: "008" },
  { id: "st9", name: "Ananya Das", rollNumber: "009" },
  { id: "st10", name: "Rohan Joshi", rollNumber: "010" },
];

const STATUS_CONFIG: Record<AttendanceStatus, { label: string; icon: React.ElementType; color: string; bgColor: string }> = {
  present: { label: "Present", icon: CheckCircle2, color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-900/30" },
  absent: { label: "Absent", icon: XCircle, color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-900/30" },
  late: { label: "Late", icon: Clock, color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-900/30" },
  half_day: { label: "Half Day", icon: MinusCircle, color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" },
  excused: { label: "Excused", icon: AlertCircle, color: "text-purple-600", bgColor: "bg-purple-100 dark:bg-purple-900/30" },
};

const AttendancePage = () => {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedClass, setSelectedClass] = useState<string>("");
  const [selectedSection, setSelectedSection] = useState<string>("");
  const [search, setSearch] = useState("");
  const [demoMode, setDemoMode] = useState(true);
  const [attendance, setAttendance] = useState<Record<string, AttendanceStatus>>({});
  const [isSaving, setIsSaving] = useState(false);

  // Get sections for selected class
  const selectedClassData = DEMO_CLASSES.find(c => c.id === selectedClass);
  const sections = selectedClassData?.sections || [];

  // Students with attendance status
  const students = useMemo(() => {
    return DEMO_STUDENTS.map(s => ({
      ...s,
      status: attendance[s.id],
    })).filter(s => 
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.rollNumber.includes(search)
    );
  }, [attendance, search]);

  // Stats
  const stats = useMemo(() => {
    const marked = Object.values(attendance);
    return {
      total: DEMO_STUDENTS.length,
      present: marked.filter(s => s === "present").length,
      absent: marked.filter(s => s === "absent").length,
      late: marked.filter(s => s === "late").length,
      notMarked: DEMO_STUDENTS.length - marked.length,
    };
  }, [attendance]);

  const handleStatusChange = (studentId: string, status: AttendanceStatus) => {
    setAttendance(prev => ({
      ...prev,
      [studentId]: prev[studentId] === status ? undefined : status,
    } as Record<string, AttendanceStatus>));
  };

  const handleMarkAll = (status: AttendanceStatus) => {
    const newAttendance: Record<string, AttendanceStatus> = {};
    DEMO_STUDENTS.forEach(s => {
      newAttendance[s.id] = status;
    });
    setAttendance(newAttendance);
    toast({ title: `Marked all as ${STATUS_CONFIG[status].label}` });
  };

  const handleSave = async () => {
    if (Object.keys(attendance).length === 0) {
      toast({ title: "No attendance marked", description: "Please mark attendance for at least one student.", variant: "destructive" });
      return;
    }

    setIsSaving(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    toast({
      title: "Attendance saved!",
      description: `Saved ${Object.keys(attendance).length} records for ${format(selectedDate, "MMM d, yyyy")}`,
    });
    setIsSaving(false);
  };

  const handlePrevDay = () => {
    setSelectedDate(prev => new Date(prev.getTime() - 24 * 60 * 60 * 1000));
    setAttendance({});
  };

  const handleNextDay = () => {
    setSelectedDate(prev => new Date(prev.getTime() + 24 * 60 * 60 * 1000));
    setAttendance({});
  };

  const handleToday = () => {
    setSelectedDate(new Date());
    setAttendance({});
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Attendance</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Mark and manage daily attendance</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm" onClick={handleSave} disabled={isSaving || Object.keys(attendance).length === 0}>
            {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Check className="h-4 w-4 mr-1" />}
            Save Attendance
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: "Total", value: stats.total, icon: Users, color: "text-foreground" },
          { label: "Present", value: stats.present, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Absent", value: stats.absent, icon: XCircle, color: "text-red-600" },
          { label: "Late", value: stats.late, icon: Clock, color: "text-amber-600" },
          { label: "Not Marked", value: stats.notMarked, icon: MinusCircle, color: "text-muted-foreground" },
        ].map((stat) => (
          <Card key={stat.label} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
                </div>
                <stat.icon className={cn("h-8 w-8 opacity-20", stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        {/* Date Selector */}
        <Card className="flex-shrink-0">
          <CardContent className="p-3 flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={handlePrevDay}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2 min-w-[180px] justify-center">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{format(selectedDate, "EEE, MMM d, yyyy")}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={handleNextDay}>
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleToday}>
              Today
            </Button>
          </CardContent>
        </Card>

        {/* Class & Section */}
        <div className="flex gap-2 flex-1">
          <Select value={selectedClass} onValueChange={(v) => { setSelectedClass(v); setSelectedSection(""); }}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select Class" />
            </SelectTrigger>
            <SelectContent>
              {DEMO_CLASSES.map(c => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {sections.length > 0 && (
            <Select value={selectedSection} onValueChange={setSelectedSection}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Section" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sections</SelectItem>
                {sections.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search student..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Quick Mark:</span>
        {(["present", "absent", "late"] as AttendanceStatus[]).map(status => {
          const config = STATUS_CONFIG[status];
          return (
            <Button
              key={status}
              variant="outline"
              size="sm"
              onClick={() => handleMarkAll(status)}
              className={cn("gap-1", config.color)}
            >
              <config.icon className="h-3.5 w-3.5" />
              All {config.label}
            </Button>
          );
        })}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setAttendance({})}
          className="text-muted-foreground"
        >
          Clear All
        </Button>
      </div>

      {/* Attendance Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-border bg-card overflow-hidden"
      >
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40">
              <TableHead className="w-[60px]">Roll</TableHead>
              <TableHead>Student</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="w-[300px] text-center">Quick Mark</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                  {selectedClass ? "No students found" : "Select a class to view students"}
                </TableCell>
              </TableRow>
            ) : (
              students.map((student, i) => (
                <motion.tr
                  key={student.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="border-b border-border hover:bg-muted/30 transition-colors"
                >
                  <TableCell className="font-mono text-sm">{student.rollNumber}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
                          {student.name.split(" ").map(n => n[0]).join("")}
                        </AvatarFallback>
                      </Avatar>
                      <span className="font-medium text-sm">{student.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    {student.status ? (
                      <Badge className={cn("gap-1", STATUS_CONFIG[student.status].bgColor, STATUS_CONFIG[student.status].color)}>
                        {React.createElement(STATUS_CONFIG[student.status].icon, { className: "h-3 w-3" })}
                        {STATUS_CONFIG[student.status].label}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-muted-foreground">Not Marked</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-center gap-1">
                      <TooltipProvider>
                        {(Object.keys(STATUS_CONFIG) as AttendanceStatus[]).map(status => {
                          const config = STATUS_CONFIG[status];
                          const isSelected = student.status === status;
                          return (
                            <Tooltip key={status}>
                              <TooltipTrigger asChild>
                                <Button
                                  variant={isSelected ? "default" : "ghost"}
                                  size="icon"
                                  className={cn(
                                    "h-8 w-8 rounded-full transition-all",
                                    isSelected ? config.bgColor : "hover:bg-muted",
                                    isSelected && config.color
                                  )}
                                  onClick={() => handleStatusChange(student.id, status)}
                                >
                                  <config.icon className={cn("h-4 w-4", isSelected ? config.color : "text-muted-foreground")} />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent side="top">
                                <p>{config.label}</p>
                              </TooltipContent>
                            </Tooltip>
                          );
                        })}
                      </TooltipProvider>
                    </div>
                  </TableCell>
                </motion.tr>
              ))
            )}
          </TableBody>
        </Table>
      </motion.div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span>Legend:</span>
        {Object.entries(STATUS_CONFIG).map(([status, config]) => (
          <div key={status} className="flex items-center gap-1">
            <config.icon className={cn("h-3.5 w-3.5", config.color)} />
            <span>{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AttendancePage;
