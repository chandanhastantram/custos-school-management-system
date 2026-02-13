import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { 
  HelpCircle, Plus, Search, Sparkles, Edit, Trash2, Copy,
  MoreHorizontal, Loader2, Filter, Download
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { teacherApi, type Question } from "@/services/teacher-api";

const QuestionBankPage = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [questionDialog, setQuestionDialog] = useState(false);
  const [aiDialog, setAIDialog] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [difficultyFilter, setDifficultyFilter] = useState("all");

  // Fetch questions
  const { data: questions = [], isLoading, refetch } = useQuery({
    queryKey: ["questions", difficultyFilter],
    queryFn: () => teacherApi.getQuestions({ 
      difficulty: difficultyFilter !== "all" ? difficultyFilter : undefined 
    }),
    retry: 1,
  });

  // Mutations
  const createQuestionMutation = useMutation({
    mutationFn: teacherApi.createQuestion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      toast({ title: "Question created successfully" });
      setQuestionDialog(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const generateQuestionsMutation = useMutation({
    mutationFn: teacherApi.generateQuestions,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      toast({ title: `Generated ${data.length} questions successfully` });
      setAIDialog(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Handlers
  const handleCreateQuestion = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      subject_id: formData.get("subject_id") as string,
      question_text: formData.get("question_text") as string,
      question_type: formData.get("question_type") as string,
      difficulty: formData.get("difficulty") as string,
      bloom_level: formData.get("bloom_level") as string,
      marks: parseInt(formData.get("marks") as string),
    };

    createQuestionMutation.mutate(data);
  };

  const handleAIGenerate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      subject: formData.get("subject") as string,
      topic: formData.get("topic") as string,
      count: parseInt(formData.get("count") as string),
      difficulty: formData.get("difficulty") as string,
    };

    generateQuestionsMutation.mutate(data);
  };

  // Filter questions
  const filteredQuestions = questions.filter(q =>
    q.question_text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate stats
  const stats = {
    total: questions.length,
    mcq: questions.filter(q => q.question_type === "mcq").length,
    short: questions.filter(q => q.question_type === "short_answer").length,
    essay: questions.filter(q => q.question_type === "essay").length,
  };

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <HelpCircle className="h-8 w-8 text-primary" />
              Question Bank
            </h1>
            <p className="text-muted-foreground mt-1">Create and manage assessment questions</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" onClick={() => setAIDialog(true)}>
              <Sparkles className="h-4 w-4 mr-2" />
              AI Generate
            </Button>
            <Button onClick={() => setQuestionDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Question
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Questions</CardDescription>
              <CardTitle className="text-3xl">{stats.total}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>MCQ</CardDescription>
              <CardTitle className="text-3xl">{stats.mcq}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Short Answer</CardDescription>
              <CardTitle className="text-3xl">{stats.short}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Essay</CardDescription>
              <CardTitle className="text-3xl">{stats.essay}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={difficultyFilter} onValueChange={setDifficultyFilter}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Difficulty" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Levels</SelectItem>
              <SelectItem value="easy">Easy</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="hard">Hard</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Questions Table */}
        <Card>
          <CardHeader>
            <CardTitle>Question Library</CardTitle>
            <CardDescription>All your assessment questions</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredQuestions.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <HelpCircle className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>No questions found</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Question</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Difficulty</TableHead>
                    <TableHead>Bloom's Level</TableHead>
                    <TableHead>Marks</TableHead>
                    <TableHead className="w-[60px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredQuestions.map((question) => (
                    <TableRow key={question.id}>
                      <TableCell className="font-medium max-w-md">
                        <p className="truncate">{question.question_text}</p>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{question.question_type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          question.difficulty === "hard" ? "destructive" : 
                          question.difficulty === "medium" ? "default" : "secondary"
                        }>
                          {question.difficulty}
                        </Badge>
                      </TableCell>
                      <TableCell>{question.bloom_level}</TableCell>
                      <TableCell>{question.marks}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Edit className="h-3.5 w-3.5 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Copy className="h-3.5 w-3.5 mr-2" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive focus:text-destructive">
                              <Trash2 className="h-3.5 w-3.5 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Add Question Dialog */}
        <Dialog open={questionDialog} onOpenChange={setQuestionDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Question</DialogTitle>
              <DialogDescription>Create a new assessment question</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateQuestion}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="question_text">Question Text</Label>
                  <Textarea 
                    id="question_text" 
                    name="question_text" 
                    placeholder="Enter the question..." 
                    required 
                    rows={4}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="question_type">Type</Label>
                    <Select name="question_type" defaultValue="mcq">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mcq">Multiple Choice</SelectItem>
                        <SelectItem value="short_answer">Short Answer</SelectItem>
                        <SelectItem value="essay">Essay</SelectItem>
                        <SelectItem value="true_false">True/False</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="difficulty">Difficulty</Label>
                    <Select name="difficulty" defaultValue="medium">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">Easy</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="bloom_level">Bloom's Level</Label>
                    <Select name="bloom_level" defaultValue="remember">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="remember">Remember</SelectItem>
                        <SelectItem value="understand">Understand</SelectItem>
                        <SelectItem value="apply">Apply</SelectItem>
                        <SelectItem value="analyze">Analyze</SelectItem>
                        <SelectItem value="evaluate">Evaluate</SelectItem>
                        <SelectItem value="create">Create</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="marks">Marks</Label>
                    <Input 
                      id="marks" 
                      name="marks" 
                      type="number" 
                      defaultValue="1" 
                      min="1"
                      required 
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="subject_id">Subject ID</Label>
                  <Input 
                    id="subject_id" 
                    name="subject_id" 
                    placeholder="Enter subject ID" 
                    required 
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setQuestionDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createQuestionMutation.isPending}>
                  {createQuestionMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Question
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* AI Generate Dialog */}
        <Dialog open={aiDialog} onOpenChange={setAIDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>AI Question Generator</DialogTitle>
              <DialogDescription>Generate questions automatically using AI</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAIGenerate}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="subject">Subject</Label>
                  <Input id="subject" name="subject" placeholder="e.g., Mathematics" required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="topic">Topic</Label>
                  <Input id="topic" name="topic" placeholder="e.g., Quadratic Equations" required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="count">Number of Questions</Label>
                    <Input id="count" name="count" type="number" defaultValue="5" min="1" max="20" required />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ai_difficulty">Difficulty</Label>
                    <Select name="difficulty" defaultValue="medium">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="easy">Easy</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setAIDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={generateQuestionsMutation.isPending}>
                  {generateQuestionsMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Generate
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </motion.div>
    </div>
  );
};

export default QuestionBankPage;
