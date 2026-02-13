import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  GraduationCap, Book, Users, Calendar, Plus, MoreHorizontal,
  Edit, Trash2, ChevronRight, Search, Filter, Download, Loader2,
  BookOpen, Clock, MapPin, User, CheckCircle2,
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
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "@/components/ui/tabs";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// Types
interface AcademicYear {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

interface ClassData {
  id: string;
  name: string;
  grade: number;
  sections: Section[];
  studentCount: number;
  subjectCount: number;
}

interface Section {
  id: string;
  name: string;
  classTeacherId?: string;
  classTeacherName?: string;
  studentCount: number;
  room?: string;
}

interface Subject {
  id: string;
  name: string;
  code: string;
  type: "core" | "elective" | "lab";
  credits: number;
  teacherName?: string;
  periodsPerWeek: number;
}

// Demo data
const DEMO_YEARS: AcademicYear[] = [
  { id: "y1", name: "2024-25", startDate: "2024-04-01", endDate: "2025-03-31", isCurrent: true },
  { id: "y2", name: "2023-24", startDate: "2023-04-01", endDate: "2024-03-31", isCurrent: false },
];

const DEMO_CLASSES: ClassData[] = [
  { id: "c1", name: "Class 10", grade: 10, sections: [
    { id: "s1", name: "A", classTeacherName: "Mrs. Sharma", studentCount: 30, room: "101" },
    { id: "s2", name: "B", classTeacherName: "Mr. Verma", studentCount: 28, room: "102" },
  ], studentCount: 58, subjectCount: 8 },
  { id: "c2", name: "Class 9", grade: 9, sections: [
    { id: "s3", name: "A", classTeacherName: "Mrs. Patel", studentCount: 32, room: "201" },
    { id: "s4", name: "B", classTeacherName: "Mr. Singh", studentCount: 30, room: "202" },
    { id: "s5", name: "C", classTeacherName: "Mrs. Gupta", studentCount: 29, room: "203" },
  ], studentCount: 91, subjectCount: 8 },
  { id: "c3", name: "Class 8", grade: 8, sections: [
    { id: "s6", name: "A", classTeacherName: "Mr. Kumar", studentCount: 35, room: "301" },
    { id: "s7", name: "B", classTeacherName: "Mrs. Reddy", studentCount: 33, room: "302" },
  ], studentCount: 68, subjectCount: 7 },
  { id: "c4", name: "Class 7", grade: 7, sections: [
    { id: "s8", name: "A", classTeacherName: "Mrs. Das", studentCount: 34, room: "401" },
  ], studentCount: 34, subjectCount: 7 },
];

const DEMO_SUBJECTS: Subject[] = [
  { id: "sub1", name: "Mathematics", code: "MATH", type: "core", credits: 5, teacherName: "Mr. Sharma", periodsPerWeek: 6 },
  { id: "sub2", name: "Science", code: "SCI", type: "core", credits: 5, teacherName: "Mrs. Verma", periodsPerWeek: 6 },
  { id: "sub3", name: "English", code: "ENG", type: "core", credits: 4, teacherName: "Mr. Patel", periodsPerWeek: 5 },
  { id: "sub4", name: "Hindi", code: "HIN", type: "core", credits: 4, teacherName: "Mrs. Singh", periodsPerWeek: 5 },
  { id: "sub5", name: "Social Science", code: "SST", type: "core", credits: 4, teacherName: "Mr. Gupta", periodsPerWeek: 4 },
  { id: "sub6", name: "Computer Science", code: "CS", type: "elective", credits: 3, teacherName: "Mr. Kumar", periodsPerWeek: 3 },
  { id: "sub7", name: "Physics Lab", code: "PHY-L", type: "lab", credits: 2, teacherName: "Mrs. Das", periodsPerWeek: 2 },
  { id: "sub8", name: "Chemistry Lab", code: "CHM-L", type: "lab", credits: 2, teacherName: "Mr. Joshi", periodsPerWeek: 2 },
];

const SUBJECT_TYPE_CONFIG: Record<Subject["type"], { label: string; color: string }> = {
  core: { label: "Core", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" },
  elective: { label: "Elective", color: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300" },
  lab: { label: "Lab", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" },
};

const AcademicsPage = () => {
  const [tab, setTab] = useState("classes");
  const [search, setSearch] = useState("");
  const [selectedYear, setSelectedYear] = useState<AcademicYear>(DEMO_YEARS[0]);
  const [demoMode] = useState(true);

  // Stats
  const stats = useMemo(() => ({
    totalClasses: DEMO_CLASSES.length,
    totalSections: DEMO_CLASSES.reduce((sum, c) => sum + c.sections.length, 0),
    totalStudents: DEMO_CLASSES.reduce((sum, c) => sum + c.studentCount, 0),
    totalSubjects: DEMO_SUBJECTS.length,
  }), []);

  // Filter classes
  const filteredClasses = useMemo(() => {
    return DEMO_CLASSES.filter((c) =>
      c.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  // Filter subjects
  const filteredSubjects = useMemo(() => {
    return DEMO_SUBJECTS.filter((s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.code.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Academics</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Manage classes, sections, and subjects</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="px-3 py-1">
            <Calendar className="h-3.5 w-3.5 mr-1.5" />
            {selectedYear.name}
          </Badge>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" /> Add Class
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Classes", value: stats.totalClasses, icon: GraduationCap, color: "text-blue-600" },
          { label: "Sections", value: stats.totalSections, icon: Users, color: "text-purple-600" },
          { label: "Students", value: stats.totalStudents, icon: User, color: "text-emerald-600" },
          { label: "Subjects", value: stats.totalSubjects, icon: BookOpen, color: "text-amber-600" },
        ].map((stat) => (
          <Card key={stat.label} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
                </div>
                <div className={cn("h-10 w-10 rounded-full flex items-center justify-center", stat.color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
                  <stat.icon className={cn("h-5 w-5", stat.color)} />
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
            <TabsTrigger value="classes">Classes & Sections</TabsTrigger>
            <TabsTrigger value="subjects">Subjects</TabsTrigger>
            <TabsTrigger value="curriculum">Curriculum</TabsTrigger>
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

        {/* Classes Tab */}
        <TabsContent value="classes" className="space-y-4">
          <Accordion type="multiple" className="space-y-3">
            {filteredClasses.map((cls) => (
              <AccordionItem key={cls.id} value={cls.id} className="border rounded-lg overflow-hidden bg-card">
                <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50">
                  <div className="flex items-center justify-between w-full pr-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <GraduationCap className="h-5 w-5 text-primary" />
                      </div>
                      <div className="text-left">
                        <p className="font-medium">{cls.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {cls.sections.length} sections · {cls.studentCount} students
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{cls.subjectCount} subjects</Badge>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {cls.sections.map((section) => (
                      <Card key={section.id} className="relative overflow-hidden">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium">Section {section.name}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                <User className="h-3 w-3 inline mr-1" />
                                {section.classTeacherName || "No class teacher"}
                              </p>
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-7 w-7">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Edit className="h-3.5 w-3.5 mr-2" /> Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <Users className="h-3.5 w-3.5 mr-2" /> View Students
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="text-destructive">
                                  <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                          <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" /> {section.studentCount}
                            </span>
                            {section.room && (
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" /> Room {section.room}
                              </span>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    <Card className="border-dashed">
                      <CardContent className="p-4 flex items-center justify-center min-h-[100px]">
                        <Button variant="ghost" className="text-muted-foreground">
                          <Plus className="h-4 w-4 mr-1" /> Add Section
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </TabsContent>

        {/* Subjects Tab */}
        <TabsContent value="subjects" className="space-y-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Subject</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Credits</TableHead>
                  <TableHead>Teacher</TableHead>
                  <TableHead>Periods/Week</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSubjects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No subjects found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredSubjects.map((subject, i) => (
                    <motion.tr
                      key={subject.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="border-b border-border hover:bg-muted/30 transition-colors"
                    >
                      <TableCell className="font-medium">{subject.name}</TableCell>
                      <TableCell className="font-mono text-sm">{subject.code}</TableCell>
                      <TableCell>
                        <Badge className={cn("gap-1", SUBJECT_TYPE_CONFIG[subject.type].color)}>
                          {SUBJECT_TYPE_CONFIG[subject.type].label}
                        </Badge>
                      </TableCell>
                      <TableCell>{subject.credits}</TableCell>
                      <TableCell className="text-sm">{subject.teacherName || "-"}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                          {subject.periodsPerWeek}
                        </div>
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
                              <Edit className="h-3.5 w-3.5 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Book className="h-3.5 w-3.5 mr-2" /> Syllabus
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </motion.tr>
                  ))
                )}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>

        {/* Curriculum Tab */}
        <TabsContent value="curriculum" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Curriculum Overview</CardTitle>
              <CardDescription>Track syllabus completion across subjects</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {DEMO_SUBJECTS.slice(0, 5).map((subject) => {
                  const progress = Math.floor(40 + Math.random() * 50);
                  return (
                    <div key={subject.id} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{subject.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">{progress}% complete</span>
                          {progress >= 75 && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                        </div>
                      </div>
                      <Progress value={progress} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AcademicsPage;
