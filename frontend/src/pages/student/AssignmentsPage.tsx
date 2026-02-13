import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  FileText, Calendar, Upload, CheckCircle2, 
  Clock, AlertCircle, Download, ExternalLink,
  Filter, Search, BookOpen, Award
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { 
  Dialog, DialogContent, DialogHeader, 
  DialogTitle, DialogDescription, DialogFooter 
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

// Types
interface Assignment {
  id: string;
  title: string;
  subject: string;
  description: string;
  dueDate: string;
  status: "pending" | "submitted" | "graded" | "late";
  score?: number;
  totalMarks: number;
  feedback?: string;
  fileUrl?: string;
}

const DEMO_ASSIGNMENTS: Assignment[] = [
  {
    id: "1",
    title: "Quadratic Equations Practice",
    subject: "Mathematics",
    description: "Complete exercises 4.1 to 4.4 from the textbook. Show all steps for derivation.",
    dueDate: "2024-11-20T10:30:00",
    status: "pending",
    totalMarks: 50,
  },
  {
    id: "2",
    title: "Chemical Reactions Lab Report",
    subject: "Science",
    description: "Submit the observations and conclusions from our experiment on exothermic reactions.",
    dueDate: "2024-11-18T14:45:00",
    status: "submitted",
    totalMarks: 30,
    fileUrl: "lab_report.pdf",
  },
  {
    id: "3",
    title: "Essay on Climate Change",
    subject: "English",
    description: "Write a 500-word essay on the impact of global warming on coastal cities.",
    dueDate: "2024-11-15T09:00:00",
    status: "graded",
    score: 28,
    totalMarks: 30,
    feedback: "Excellent analysis. Good use of statistics. Watch your punctuation in the 3rd paragraph.",
    fileUrl: "climate_essay.docx",
  },
  {
    id: "4",
    title: "Periodicity & Elements",
    subject: "Science",
    description: "Memorize the first 20 elements and their properties for a surprise quiz.",
    dueDate: "2024-11-10T11:15:00",
    status: "late",
    totalMarks: 20,
  }
];

const AssignmentsPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const filteredAssignments = DEMO_ASSIGNMENTS.filter(a => 
    a.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    a.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleFileUpload = () => {
    setIsUploading(true);
    // Simulate upload
    setTimeout(() => {
      setIsUploading(false);
      setIsSubmitModalOpen(false);
      toast.success("Assignment submitted successfully!");
    }, 2000);
  };

  const statusConfig = {
    pending: { label: "Pending", color: "text-amber-600 bg-amber-50 border-amber-200", icon: Clock },
    submitted: { label: "Submitted", color: "text-blue-600 bg-blue-50 border-blue-200", icon: CheckCircle2 },
    graded: { label: "Graded", color: "text-emerald-600 bg-emerald-50 border-emerald-200", icon: Award },
    late: { label: "Late", color: "text-red-600 bg-red-50 border-red-200", icon: AlertCircle },
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">My Assignments</h1>
          <p className="text-muted-foreground text-sm">View, track and submit your academic work</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search assignments..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-4 max-w-md">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="submitted">Submitted</TabsTrigger>
          <TabsTrigger value="graded">Graded</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredAssignments.map((assignment, i) => {
              const config = statusConfig[assignment.status];
              return (
                <motion.div
                  key={assignment.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="h-full flex flex-col hover:shadow-lg transition-shadow border-2 hover:border-primary/20">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <Badge variant="outline" className={cn("text-[10px] py-0", config.color)}>
                          <config.icon className="h-3 w-3 mr-1" />
                          {config.label}
                        </Badge>
                        <span className="text-xs text-muted-foreground flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {format(new Date(assignment.dueDate), "MMM d, h:mm a")}
                        </span>
                      </div>
                      <CardTitle className="text-lg mt-2 line-clamp-1">{assignment.title}</CardTitle>
                      <CardDescription className="flex items-center gap-1">
                        <BookOpen className="h-3 w-3" /> {assignment.subject}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 pb-4">
                      <p className="text-sm text-muted-foreground line-clamp-2 mt-2">
                        {assignment.description}
                      </p>
                      
                      {assignment.status === "graded" && (
                        <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-950/20 rounded-lg border border-emerald-100 dark:border-emerald-900/30">
                          <div className="flex items-center justify-between font-bold text-emerald-700 dark:text-emerald-400">
                            <span>Score</span>
                            <span>{assignment.score}/{assignment.totalMarks}</span>
                          </div>
                          <Progress value={(assignment.score! / assignment.totalMarks) * 100} className="h-1.5 mt-2" />
                        </div>
                      )}

                      {assignment.status === "pending" && (
                        <div className="mt-4 space-y-2">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Time Left</span>
                            <span className="text-amber-600 font-medium">2 days</span>
                          </div>
                          <Progress value={40} className="h-1.5" />
                        </div>
                      )}
                    </CardContent>
                    <div className="p-4 pt-0 mt-auto">
                      <Button 
                        className="w-full" 
                        variant={assignment.status === "pending" ? "default" : "outline"}
                        onClick={() => {
                          setSelectedAssignment(assignment);
                          if (assignment.status === "pending" || assignment.status === "late") {
                            setIsSubmitModalOpen(true);
                          }
                        }}
                      >
                        {assignment.status === "pending" ? (
                          <><Upload className="h-4 w-4 mr-2" /> Submit Work</>
                        ) : (
                          <><FileText className="h-4 w-4 mr-2" /> View Details</>
                        )}
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </TabsContent>
        {/* Other TabContents would follow same pattern */}
      </Tabs>

      {/* Submit Modal */}
      <Dialog open={isSubmitModalOpen} onOpenChange={setIsSubmitModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Submit Assignment</DialogTitle>
            <DialogDescription>
              Upload your completed work for "{selectedAssignment?.title}".
              Only PDF, DOCX or ZIP files are allowed.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-xl p-8 hover:border-primary transition-colors cursor-pointer group">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              <p className="text-sm font-medium">Click or drag files here</p>
              <p className="text-xs text-muted-foreground mt-1">Maximum file size: 10MB</p>
            </div>
            {isUploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span>Uploading...</span>
                  <span>75%</span>
                </div>
                <Progress value={75} className="h-1.5" />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSubmitModalOpen(false)}>Cancel</Button>
            <Button onClick={handleFileUpload} disabled={isUploading}>
              {isUploading ? "Uploading..." : "Confirm Submission"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AssignmentsPage;
