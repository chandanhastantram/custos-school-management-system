import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  FileText, Download, Printer, Share2, 
  Search, Filter, Award, TrendingUp,
  ChevronRight, Calendar, BookOpen, GraduationCap
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const DEMO_REPORT_CARD = {
  student: {
    name: "Aisha Singh",
    rollNumber: "2024/101",
    class: "10-A",
    admissionNumber: "CUST/2024/1001",
  },
  academicYear: "2024-25",
  term: "Mid-Term",
  subjects: [
    { name: "Mathematics", maxMarks: 100, obtained: 85, grade: "A" },
    { name: "Science", maxMarks: 100, obtained: 78, grade: "B+" },
    { name: "English", maxMarks: 100, obtained: 82, grade: "A" },
    { name: "Hindi", maxMarks: 100, obtained: 75, grade: "B+" },
    { name: "Social Science", maxMarks: 100, obtained: 80, grade: "A" },
    { name: "Computer Science", maxMarks: 100, obtained: 92, grade: "A+" },
  ],
  attendance: {
    totalDays: 120,
    present: 112,
    percentage: 93.3,
  },
  remarks: "Excellent performance. Keep up the good work!"
};

const ReportCardsPage = () => {
  const [selectedTerm, setSelectedTerm] = useState("mid-term");

  const totalObtained = DEMO_REPORT_CARD.subjects.reduce((acc, s) => acc + s.obtained, 0);
  const totalMax = DEMO_REPORT_CARD.subjects.reduce((acc, s) => acc + s.maxMarks, 0);
  const percentage = (totalObtained / totalMax) * 100;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Academic Results</h1>
          <p className="text-muted-foreground text-sm">View and download your official report cards</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Printer className="h-4 w-4 mr-2" /> Print
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" /> Download PDF
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Summary Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader className="pb-3 text-center">
              <Avatar className="h-20 w-20 mx-auto mb-2 border-4 border-primary/10">
                <AvatarFallback className="bg-primary/5 text-2xl font-bold text-primary">AS</AvatarFallback>
              </Avatar>
              <CardTitle className="text-lg">{DEMO_REPORT_CARD.student.name}</CardTitle>
              <CardDescription>Class {DEMO_REPORT_CARD.student.class}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <p className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider">Overall Performance</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-primary">{percentage.toFixed(1)}%</span>
                  <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 border-emerald-200">A Grade</Badge>
                </div>
              </div>
              
              <div className="pt-2 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground flex items-center gap-2">
                    <Calendar className="h-4 w-4" /> Attendance
                  </span>
                  <span className="font-medium text-emerald-600 font-mono">{DEMO_REPORT_CARD.attendance.percentage}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" /> Rank
                  </span>
                  <span className="font-medium font-mono">#5/45</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary/5 border-primary/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Teacher's Remarks</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm italic text-muted-foreground">
                "{DEMO_REPORT_CARD.remarks}"
              </p>
              <div className="mt-4 flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-primary/10" />
                <div>
                  <p className="text-xs font-semibold">Mr. S. Kumar</p>
                  <p className="text-[10px] text-muted-foreground">Class Teacher</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Report Table */}
        <div className="lg:col-span-3 space-y-6">
          <Tabs defaultValue="mid-term" className="w-full">
            <TabsList>
              <TabsTrigger value="mid-term">Mid-Term 2024-25</TabsTrigger>
              <TabsTrigger value="half-yearly">Half-Yearly 2024-25</TabsTrigger>
              <TabsTrigger value="annual" disabled>Annual 2024-25</TabsTrigger>
            </TabsList>
            
            <TabsContent value="mid-term" className="mt-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="text-base">Subject-wise Performance</CardTitle>
                    <CardDescription>Academic assessment for {DEMO_REPORT_CARD.term}</CardDescription>
                  </div>
                  <Badge variant="secondary" className="px-3 py-1 uppercase tracking-tighter">Official Copy</Badge>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader className="bg-muted/50">
                        <TableRow>
                          <TableHead className="w-[200px]">Subject</TableHead>
                          <TableHead className="text-center">Max Marks</TableHead>
                          <TableHead className="text-center">Obtained</TableHead>
                          <TableHead>Grade</TableHead>
                          <TableHead className="text-right">Performance</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {DEMO_REPORT_CARD.subjects.map((sub) => (
                          <TableRow key={sub.name} className="hover:bg-muted/30">
                            <TableCell className="font-medium">
                              <div className="flex items-center gap-2">
                                <BookOpen className="h-4 w-4 text-muted-foreground" />
                                {sub.name}
                              </div>
                            </TableCell>
                            <TableCell className="text-center font-mono">{sub.maxMarks}</TableCell>
                            <TableCell className="text-center font-bold font-mono">{sub.obtained}</TableCell>
                            <TableCell>
                              <Badge variant="outline" className={cn(
                                "font-mono font-bold",
                                sub.grade.startsWith('A') ? "text-emerald-600 border-emerald-200 bg-emerald-50" : "text-blue-600 border-blue-200 bg-blue-50"
                              )}>
                                {sub.grade}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <Progress value={(sub.obtained / sub.maxMarks) * 100} className="h-1.5 w-24 ml-auto" />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-muted/20 border-2 border-dashed">
                    <div className="text-center p-2">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground">Total Obtained</p>
                      <p className="text-xl font-bold">{totalObtained}</p>
                    </div>
                    <div className="text-center p-2">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground">Out Of</p>
                      <p className="text-xl font-bold">{totalMax}</p>
                    </div>
                    <div className="text-center p-2">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground">Percentage</p>
                      <p className="text-xl font-bold text-primary">{percentage.toFixed(1)}%</p>
                    </div>
                    <div className="text-center p-2">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground">Final Grade</p>
                      <p className="text-xl font-bold text-emerald-600">A</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default ReportCardsPage;

