import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Brain, Sparkles, Trophy, Target, Clock, CheckCircle2, XCircle, Loader2,
  TrendingUp, Award, Zap, Star, ChevronRight, BarChart3
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "@/hooks/use-toast";
import { Textarea } from "@/components/ui/textarea";
import { studentTrainerApi, type Quiz, type QuizQuestion, type QuizResult } from "@/services/student-trainer-api";

const AITrainerPage = () => {
  const queryClient = useQueryClient();
  const [selectedQuiz, setSelectedQuiz] = useState<Quiz | null>(null);
  const [quizDialog, setQuizDialog] = useState(false);
  const [resultDialog, setResultDialog] = useState(false);
  const [currentSubmissionId, setCurrentSubmissionId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);

  // Timer effect
  useEffect(() => {
    if (timeRemaining === null || timeRemaining <= 0) return;
    
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev === null || prev <= 1) {
          handleSubmitQuiz();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

  // Fetch available quizzes
  const { data: quizzesData, isLoading } = useQuery({
    queryKey: ["student-quizzes"],
    queryFn: () => studentTrainerApi.listQuizzes({ status: "published" }),
  });

  // Fetch quiz stats
  const { data: stats } = useQuery({
    queryKey: ["student-quiz-stats"],
    queryFn: () => studentTrainerApi.getMyStats(),
  });

  // Start quiz mutation
  const startQuizMutation = useMutation({
    mutationFn: (quizId: string) => studentTrainerApi.startQuiz(quizId),
    onSuccess: (data) => {
      setCurrentSubmissionId(data.submission_id);
      if (data.time_limit_minutes) {
        setTimeRemaining(data.time_limit_minutes * 60);
      }
      setQuizDialog(true);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Submit quiz mutation
  const submitQuizMutation = useMutation({
    mutationFn: ({ submissionId, answers }: { submissionId: string; answers: Record<string, any> }) =>
      studentTrainerApi.submitQuiz(submissionId, answers),
    onSuccess: (result) => {
      setQuizResult(result);
      setQuizDialog(false);
      setResultDialog(true);
      queryClient.invalidateQueries({ queryKey: ["student-quizzes"] });
      queryClient.invalidateQueries({ queryKey: ["student-quiz-stats"] });
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const handleStartQuiz = async (quiz: Quiz) => {
    setSelectedQuiz(quiz);
    setAnswers({});
    setQuizQuestions([]);
    
    try {
      // Start the quiz
      const startData = await studentTrainerApi.startQuiz(quiz.id);
      setCurrentSubmissionId(startData.submission_id);
      
      if (startData.time_limit_minutes) {
        setTimeRemaining(startData.time_limit_minutes * 60);
      }
      
      // Fetch quiz questions
      const quizData = await studentTrainerApi.getQuiz(quiz.id);
      setQuizQuestions(quizData.questions || []);
      
      setQuizDialog(true);
    } catch (error: any) {
      toast({ 
        title: "Error", 
        description: error.message || "Failed to start quiz", 
        variant: "destructive" 
      });
    }
  };

  const handleSubmitQuiz = () => {
    if (!currentSubmissionId) return;
    
    if (confirm("Are you sure you want to submit? You cannot change your answers after submission.")) {
      submitQuizMutation.mutate({ submissionId: currentSubmissionId, answers });
    }
  };

  const handleAnswerChange = (questionId: string, answer: any) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "bg-emerald-500";
      case "medium": return "bg-amber-500";
      case "hard": return "bg-rose-500";
      default: return "bg-gray-500";
    }
  };

  const getDifficultyGradient = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "from-emerald-500 to-teal-500";
      case "medium": return "from-amber-500 to-orange-500";
      case "hard": return "from-rose-500 to-pink-500";
      default: return "from-gray-500 to-slate-500";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-purple-50 to-fuchsia-50 dark:from-violet-950 dark:via-purple-950 dark:to-fuchsia-950">
      <div className="container py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Hero Header */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600 p-8 text-white shadow-2xl">
            <div className="absolute inset-0 bg-grid-white/10"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
            <div className="relative z-10">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="flex items-center justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl bg-white/20 p-3 backdrop-blur-sm">
                      <Brain className="h-8 w-8" />
                    </div>
                    <div>
                      <h1 className="text-4xl font-bold tracking-tight">CUSTOS AI Trainer</h1>
                      <p className="text-purple-100 mt-1">Master your subjects with AI-powered quizzes</p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="rounded-2xl bg-white/20 backdrop-blur-sm px-6 py-3 border border-white/30">
                    <div className="flex items-center gap-2">
                      <Trophy className="h-6 w-6 text-yellow-300" />
                      <div>
                        <div className="text-2xl font-bold">{stats?.total_quizzes_passed || 0}</div>
                        <div className="text-xs text-purple-100">Quizzes Passed</div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Stats Grid */}
              {stats && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="grid grid-cols-4 gap-4 mt-6"
                >
                  <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-white/20 p-2">
                        <Target className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{stats.total_quizzes_taken}</div>
                        <div className="text-sm text-purple-100">Quizzes Taken</div>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-white/20 p-2">
                        <TrendingUp className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{stats.average_percentage.toFixed(1)}%</div>
                        <div className="text-sm text-purple-100">Avg Score</div>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-white/20 p-2">
                        <BarChart3 className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="text-2xl font-bold">
                          {stats.total_quizzes_taken > 0 
                            ? ((stats.total_quizzes_passed / stats.total_quizzes_taken) * 100).toFixed(0)
                            : 0}%
                        </div>
                        <div className="text-sm text-purple-100">Pass Rate</div>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-white/20 p-2">
                        <Clock className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{stats.total_time_spent_minutes}</div>
                        <div className="text-sm text-purple-100">Minutes</div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Available Quizzes */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="border-2 shadow-xl rounded-2xl overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-900 dark:to-purple-900 border-b-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-6 w-6 text-primary" />
                  <div>
                    <CardTitle className="text-2xl">Available Quizzes</CardTitle>
                    <CardDescription className="text-base">AI-generated quizzes tailored to your syllabus</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-20">
                    <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                    <p className="text-muted-foreground">Loading quizzes...</p>
                  </div>
                ) : quizzesData?.items.length === 0 ? (
                  <div className="text-center py-20">
                    <div className="rounded-full bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900 dark:to-purple-900 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                      <Target className="h-12 w-12 text-violet-600 dark:text-violet-400" />
                    </div>
                    <h3 className="text-2xl font-semibold mb-2">No quizzes available yet</h3>
                    <p className="text-muted-foreground">Check back soon for new AI-generated quizzes!</p>
                  </div>
                ) : (
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    <AnimatePresence>
                      {quizzesData?.items.map((quiz, index) => (
                        <motion.div
                          key={quiz.id}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <Card className="group hover:shadow-2xl transition-all duration-300 border-2 hover:border-primary/50 rounded-2xl overflow-hidden h-full">
                            <div className={`h-2 bg-gradient-to-r ${getDifficultyGradient(quiz.difficulty)}`}></div>
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between gap-2">
                                <CardTitle className="text-lg line-clamp-2 group-hover:text-primary transition-colors">
                                  {quiz.title}
                                </CardTitle>
                                <Badge className={`${getDifficultyColor(quiz.difficulty)} text-white shrink-0`}>
                                  {quiz.difficulty}
                                </Badge>
                              </div>
                              <CardDescription className="line-clamp-2 mt-2">
                                {quiz.description}
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                <div className="rounded-lg bg-muted p-3">
                                  <div className="text-muted-foreground text-xs mb-1">Questions</div>
                                  <div className="font-bold text-lg">{quiz.total_questions}</div>
                                </div>
                                <div className="rounded-lg bg-muted p-3">
                                  <div className="text-muted-foreground text-xs mb-1">Total Marks</div>
                                  <div className="font-bold text-lg">{quiz.total_marks}</div>
                                </div>
                              </div>

                              {quiz.time_limit_minutes && (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 rounded-lg p-2">
                                  <Clock className="h-4 w-4" />
                                  <span className="font-medium">{quiz.time_limit_minutes} minutes</span>
                                </div>
                              )}

                              {quiz.ai_generated && (
                                <Badge variant="outline" className="w-full justify-center py-2 bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-950 dark:to-purple-950 border-violet-200 dark:border-violet-800">
                                  <Sparkles className="h-3 w-3 mr-1 text-violet-600 dark:text-violet-400" />
                                  <span className="text-violet-600 dark:text-violet-400">AI Generated</span>
                                </Badge>
                              )}

                              <Button 
                                className={`w-full bg-gradient-to-r ${getDifficultyGradient(quiz.difficulty)} hover:opacity-90 transition-opacity shadow-lg`}
                                onClick={() => handleStartQuiz(quiz)}
                                disabled={startQuizMutation.isPending}
                                size="lg"
                              >
                                {startQuizMutation.isPending ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Starting...
                                  </>
                                ) : (
                                  <>
                                    <Zap className="h-4 w-4 mr-2" />
                                    Start Quiz
                                  </>
                                )}
                              </Button>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Quiz Taking Dialog */}
        <Dialog open={quizDialog} onOpenChange={setQuizDialog}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl">{selectedQuiz?.title}</DialogTitle>
              <DialogDescription className="text-base">
                Answer all questions to the best of your ability
              </DialogDescription>
            </DialogHeader>
            
            {timeRemaining !== null && (
              <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 rounded-xl border-2 border-orange-200 dark:border-orange-800">
                <Clock className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                <div className="flex-1">
                  <div className="text-sm text-muted-foreground">Time Remaining</div>
                  <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                  </div>
                </div>
                <Progress 
                  value={(timeRemaining / ((selectedQuiz?.time_limit_minutes || 1) * 60)) * 100} 
                  className="w-32"
                />
              </div>
            )}

            <div className="space-y-6 py-4">
              {quizQuestions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
                  <p className="text-muted-foreground">Loading questions...</p>
                </div>
              ) : (
                quizQuestions.map((question, index) => (
                  <div key={question.id} className="p-5 bg-muted/30 rounded-xl border-2 border-border">
                    <div className="flex items-start gap-3 mb-4">
                      <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold shrink-0">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-base font-medium leading-relaxed">{question.question_text}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">{question.marks} {question.marks === 1 ? 'mark' : 'marks'}</Badge>
                          {question.difficulty && (
                            <Badge className={`text-xs ${getDifficultyColor(question.difficulty)} text-white`}>
                              {question.difficulty}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Answer Input */}
                    <div className="ml-11">
                      {question.question_type === "mcq" && question.options ? (
                        <RadioGroup
                          value={answers[question.id] || ""}
                          onValueChange={(value) => handleAnswerChange(question.id, value)}
                        >
                          <div className="space-y-2">
                            {question.options.map((option) => (
                              <div key={option.id} className="flex items-center space-x-2 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                                <RadioGroupItem value={option.id} id={`${question.id}-${option.id}`} />
                                <Label htmlFor={`${question.id}-${option.id}`} className="flex-1 cursor-pointer">
                                  <span className="font-medium mr-2">{option.id}.</span>
                                  {option.text}
                                </Label>
                              </div>
                            ))}
                          </div>
                        </RadioGroup>
                      ) : question.question_type === "true_false" ? (
                        <RadioGroup
                          value={answers[question.id] || ""}
                          onValueChange={(value) => handleAnswerChange(question.id, value)}
                        >
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2 p-3 rounded-lg hover:bg-muted/50">
                              <RadioGroupItem value="true" id={`${question.id}-true`} />
                              <Label htmlFor={`${question.id}-true`} className="flex-1 cursor-pointer">True</Label>
                            </div>
                            <div className="flex items-center space-x-2 p-3 rounded-lg hover:bg-muted/50">
                              <RadioGroupItem value="false" id={`${question.id}-false`} />
                              <Label htmlFor={`${question.id}-false`} className="flex-1 cursor-pointer">False</Label>
                            </div>
                          </div>
                        </RadioGroup>
                      ) : (
                        <Textarea
                          placeholder="Type your answer here..."
                          value={answers[question.id] || ""}
                          onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                          className="min-h-[100px]"
                        />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setQuizDialog(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSubmitQuiz}
                disabled={submitQuizMutation.isPending}
                className="bg-gradient-to-r from-violet-600 to-purple-600"
              >
                {submitQuizMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Submit Quiz
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Results Dialog */}
        <Dialog open={resultDialog} onOpenChange={setResultDialog}>
          <DialogContent className="max-w-2xl rounded-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3 text-2xl">
                {quizResult?.passed ? (
                  <div className="rounded-full bg-green-100 dark:bg-green-900 p-3">
                    <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
                  </div>
                ) : (
                  <div className="rounded-full bg-red-100 dark:bg-red-900 p-3">
                    <XCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
                  </div>
                )}
                <div>
                  <div>{quizResult?.passed ? "Congratulations! 🎉" : "Keep Practicing! 💪"}</div>
                  <div className="text-sm text-muted-foreground font-normal">Quiz Results</div>
                </div>
              </DialogTitle>
            </DialogHeader>

            {quizResult && (
              <div className="space-y-6 py-4">
                {/* Score Display */}
                <div className="text-center space-y-3 p-6 rounded-2xl bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950 dark:to-purple-950 border-2">
                  <div className="text-6xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                    {quizResult.percentage?.toFixed(1)}%
                  </div>
                  <div className="text-lg text-muted-foreground">
                    {quizResult.score} / {quizResult.max_score} marks
                  </div>
                  <Progress value={quizResult.percentage} className="h-3" />
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 dark:bg-green-950 rounded-xl border-2 border-green-200 dark:border-green-800">
                    <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {quizResult.correct_answers}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1 flex items-center justify-center gap-1">
                      <CheckCircle2 className="h-4 w-4" />
                      Correct
                    </div>
                  </div>
                  <div className="text-center p-4 bg-red-50 dark:bg-red-950 rounded-xl border-2 border-red-200 dark:border-red-800">
                    <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                      {quizResult.incorrect_answers}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1 flex items-center justify-center gap-1">
                      <XCircle className="h-4 w-4" />
                      Incorrect
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border-2 border-gray-200 dark:border-gray-800">
                    <div className="text-3xl font-bold">
                      {quizResult.unanswered}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">Unanswered</div>
                  </div>
                </div>

                {/* Feedback */}
                {quizResult.feedback && (
                  <div className="p-4 bg-muted rounded-xl border-2">
                    <div className="flex items-start gap-2">
                      <Star className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                      <div>
                        <div className="font-semibold mb-1">AI Feedback</div>
                        <p className="text-sm text-muted-foreground">{quizResult.feedback}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <DialogFooter>
              <Button onClick={() => setResultDialog(false)} size="lg" className="w-full">
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AITrainerPage;
