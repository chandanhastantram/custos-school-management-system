import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format, addDays } from "date-fns";
import {
  FileText, Calendar, Clock, Users, Plus, MoreHorizontal,
  Edit, Trash2, Eye, Download, Search, Filter, CheckCircle2,
  AlertCircle, BarChart3, BookOpen, Award, TrendingUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// Types
type ExamStatus = "scheduled" | "ongoing" | "completed" | "cancelled";
type ExamType = "unit_test" | "mid_term" | "final" | "practical";

interface Exam {
  id: string;
  name: string;
  type: ExamType;
  className: string;
  startDate: string;
  endDate: string;
  status: ExamStatus;
  totalSubjects: number;
  completedSubjects: number;
  totalMarks: number;
}

interface ExamResult {
  id: string;
  studentName: string;
  rollNo: string;
  className: string;
  examName: string;
  totalMarks: number;
  obtainedMarks: number;
  percentage: number;
  grade: string;
  rank: number;
}

// Demo data
const DEMO_EXAMS: Exam[] = [
  { id: "e1", name: "Unit Test 1", type: "unit_test", className: "Class 10", startDate: "2024-06-10", endDate: "2024-06-15", status: "completed", totalSubjects: 6, completedSubjects: 6, totalMarks: 300 },
  { id: "e2", name: "Mid-Term Examination", type: "mid_term", className: "Class 10", startDate: "2024-09-15", endDate: "2024-09-25", status: "completed", totalSubjects: 8, completedSubjects: 8, totalMarks: 800 },
  { id: "e3", name: "Unit Test 2", type: "unit_test", className: "Class 10", startDate: "2024-11-10", endDate: "2024-11-15", status: "ongoing", totalSubjects: 6, completedSubjects: 3, totalMarks: 300 },
  { id: "e4", name: "Final Examination", type: "final", className: "Class 10", startDate: "2025-02-20", endDate: "2025-03-05", status: "scheduled", totalSubjects: 8, completedSubjects: 0, totalMarks: 800 },
  { id: "e5", name: "Physics Practical", type: "practical", className: "Class 10", startDate: "2025-01-15", endDate: "2025-01-15", status: "scheduled", totalSubjects: 1, completedSubjects: 0, totalMarks: 30 },
];

const DEMO_RESULTS: ExamResult[] = [
  { id: "r1", studentName: "Aisha Sharma", rollNo: "10A01", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 756, percentage: 94.5, grade: "A+", rank: 1 },
  { id: "r2", studentName: "Rahul Verma", rollNo: "10A02", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 712, percentage: 89.0, grade: "A", rank: 2 },
  { id: "r3", studentName: "Priya Patel", rollNo: "10A03", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 688, percentage: 86.0, grade: "A", rank: 3 },
  { id: "r4", studentName: "Vikram Singh", rollNo: "10A04", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 640, percentage: 80.0, grade: "B+", rank: 4 },
  { id: "r5", studentName: "Nisha Gupta", rollNo: "10A05", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 592, percentage: 74.0, grade: "B", rank: 5 },
  { id: "r6", studentName: "Arjun Kumar", rollNo: "10A06", className: "Class 10-A", examName: "Mid-Term", totalMarks: 800, obtainedMarks: 544, percentage: 68.0, grade: "B", rank: 6 },
];

const STATUS_CONFIG: Record<ExamStatus, { label: string; color: string; bgColor: string }> = {
  scheduled: { label: "Scheduled", color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" },
  ongoing: { label: "Ongoing", color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-900/30" },
  completed: { label: "Completed", color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-900/30" },
  cancelled: { label: "Cancelled", color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-900/30" },
};

const TYPE_CONFIG: Record<ExamType, { label: string; icon: React.ElementType }> = {
  unit_test: { label: "Unit Test", icon: FileText },
  mid_term: { label: "Mid-Term", icon: BookOpen },
  final: { label: "Final", icon: Award },
  practical: { label: "Practical", icon: BarChart3 },
};

const GRADE_COLORS: Record<string, string> = {
  "A+": "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30",
  "A": "text-green-600 bg-green-100 dark:bg-green-900/30",
  "B+": "text-blue-600 bg-blue-100 dark:bg-blue-900/30",
  "B": "text-sky-600 bg-sky-100 dark:bg-sky-900/30",
  "C": "text-amber-600 bg-amber-100 dark:bg-amber-900/30",
  "D": "text-orange-600 bg-orange-100 dark:bg-orange-900/30",
  "F": "text-red-600 bg-red-100 dark:bg-red-900/30",
};

const ExamsPage = () => {
  const [tab, setTab] = useState("exams");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [classFilter, setClassFilter] = useState<string>("all");
  const [demoMode] = useState(true);

  // Stats
  const stats = useMemo(() => ({
    totalExams: DEMO_EXAMS.length,
    scheduled: DEMO_EXAMS.filter(e => e.status === "scheduled").length,
    ongoing: DEMO_EXAMS.filter(e => e.status === "ongoing").length,
    completed: DEMO_EXAMS.filter(e => e.status === "completed").length,
    avgPercentage: DEMO_RESULTS.length > 0 
      ? (DEMO_RESULTS.reduce((sum, r) => sum + r.percentage, 0) / DEMO_RESULTS.length).toFixed(1)
      : 0,
  }), []);

  // Filter exams
  const filteredExams = useMemo(() => {
    return DEMO_EXAMS.filter((exam) => {
      const matchesSearch = exam.name.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "all" || exam.status === statusFilter;
      const matchesClass = classFilter === "all" || exam.className === classFilter;
      return matchesSearch && matchesStatus && matchesClass;
    });
  }, [search, statusFilter, classFilter]);

  // Filter results
  const filteredResults = useMemo(() => {
    return DEMO_RESULTS.filter((result) =>
      result.studentName.toLowerCase().includes(search.toLowerCase()) ||
      result.rollNo.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Examinations</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Schedule and manage exams, view results</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export Results
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" /> Create Exam
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "Total Exams", value: stats.totalExams, icon: FileText, color: "text-blue-600" },
          { label: "Scheduled", value: stats.scheduled, icon: Calendar, color: "text-purple-600" },
          { label: "Ongoing", value: stats.ongoing, icon: Clock, color: "text-amber-600" },
          { label: "Completed", value: stats.completed, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Avg. Score", value: `${stats.avgPercentage}%`, icon: TrendingUp, color: "text-rose-600" },
        ].map((stat) => (
          <Card key={stat.label} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className={cn("text-xl font-bold", stat.color)}>{stat.value}</p>
                </div>
                <div className={cn("h-9 w-9 rounded-full flex items-center justify-center", stat.color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
                  <stat.icon className={cn("h-4 w-4", stat.color)} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="exams">Exam Schedule</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>
          <div className="flex items-center gap-2">
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            {tab === "exams" && (
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        {/* Exams Tab */}
        <TabsContent value="exams" className="space-y-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Exam</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExams.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No exams found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredExams.map((exam, i) => {
                    const TypeIcon = TYPE_CONFIG[exam.type].icon;
                    const progress = (exam.completedSubjects / exam.totalSubjects) * 100;
                    return (
                      <motion.tr
                        key={exam.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="border-b border-border hover:bg-muted/30 transition-colors"
                      >
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center">
                              <TypeIcon className="h-4 w-4 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium text-sm">{exam.name}</p>
                              <p className="text-xs text-muted-foreground">{exam.totalMarks} marks</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">{TYPE_CONFIG[exam.type].label}</TableCell>
                        <TableCell className="text-sm">{exam.className}</TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p>{format(new Date(exam.startDate), "MMM d")}</p>
                            <p className="text-xs text-muted-foreground">to {format(new Date(exam.endDate), "MMM d")}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="w-24">
                            <Progress value={progress} className="h-2" />
                            <p className="text-xs text-muted-foreground mt-1">
                              {exam.completedSubjects}/{exam.totalSubjects} subjects
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={cn("gap-1", STATUS_CONFIG[exam.status].bgColor, STATUS_CONFIG[exam.status].color)}>
                            {STATUS_CONFIG[exam.status].label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <Eye className="h-3.5 w-3.5 mr-2" /> View Schedule
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Edit className="h-3.5 w-3.5 mr-2" /> Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <BarChart3 className="h-3.5 w-3.5 mr-2" /> View Results
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive">
                                <Trash2 className="h-3.5 w-3.5 mr-2" /> Cancel
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </motion.tr>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Rank</TableHead>
                  <TableHead>Student</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead>Exam</TableHead>
                  <TableHead className="text-right">Marks</TableHead>
                  <TableHead className="text-right">Percentage</TableHead>
                  <TableHead>Grade</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredResults.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No results found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredResults.map((result, i) => (
                    <motion.tr
                      key={result.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="border-b border-border hover:bg-muted/30 transition-colors"
                    >
                      <TableCell>
                        <div className={cn(
                          "h-7 w-7 rounded-full flex items-center justify-center font-bold text-sm",
                          result.rank === 1 ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30" :
                          result.rank === 2 ? "bg-gray-100 text-gray-700 dark:bg-gray-800" :
                          result.rank === 3 ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30" :
                          "bg-muted text-muted-foreground"
                        )}>
                          {result.rank}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{result.studentName}</p>
                          <p className="text-xs text-muted-foreground">Roll: {result.rollNo}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{result.className}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{result.examName}</TableCell>
                      <TableCell className="text-right font-medium">
                        {result.obtainedMarks}/{result.totalMarks}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {result.percentage}%
                      </TableCell>
                      <TableCell>
                        <Badge className={cn("font-bold", GRADE_COLORS[result.grade] || "bg-muted")}>
                          {result.grade}
                        </Badge>
                      </TableCell>
                    </motion.tr>
                  ))
                )}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Grade Distribution</CardTitle>
                <CardDescription>Class 10-A · Mid-Term Examination</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { grade: "A+", count: 5, percentage: 17 },
                    { grade: "A", count: 8, percentage: 27 },
                    { grade: "B+", count: 7, percentage: 23 },
                    { grade: "B", count: 6, percentage: 20 },
                    { grade: "C", count: 3, percentage: 10 },
                    { grade: "D", count: 1, percentage: 3 },
                  ].map(({ grade, count, percentage }) => (
                    <div key={grade} className="flex items-center gap-3">
                      <Badge className={cn("w-10 justify-center font-bold", GRADE_COLORS[grade])}>
                        {grade}
                      </Badge>
                      <div className="flex-1">
                        <Progress value={percentage} className="h-2" />
                      </div>
                      <span className="text-sm text-muted-foreground w-16 text-right">
                        {count} ({percentage}%)
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Subject-wise Average</CardTitle>
                <CardDescription>Class 10-A · Mid-Term Examination</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { subject: "Mathematics", avg: 78 },
                    { subject: "Science", avg: 82 },
                    { subject: "English", avg: 75 },
                    { subject: "Hindi", avg: 80 },
                    { subject: "Social Science", avg: 72 },
                    { subject: "Computer Science", avg: 88 },
                  ].map(({ subject, avg }) => (
                    <div key={subject} className="flex items-center gap-3">
                      <span className="text-sm font-medium w-36 truncate">{subject}</span>
                      <div className="flex-1">
                        <Progress value={avg} className="h-2" />
                      </div>
                      <span className={cn(
                        "text-sm font-medium w-12 text-right",
                        avg >= 80 ? "text-emerald-600" : avg >= 60 ? "text-blue-600" : "text-amber-600"
                      )}>
                        {avg}%
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExamsPage;
