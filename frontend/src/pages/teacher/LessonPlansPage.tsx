import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { 
  BookOpen, Plus, Search, Sparkles, Edit, Trash2, Eye, Loader2, 
  Calendar, Clock, Target, Zap, TrendingUp, Award, ChevronRight
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { teacherApi } from "@/services/teacher-api";

const LessonPlansPage = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [planDialog, setPlanDialog] = useState(false);
  const [aiDialog, setAIDialog] = useState(false);
  const [viewDialog, setViewDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<any>(null);

  // Fetch lesson plans
  const { data: lessonPlans = [], isLoading, refetch } = useQuery({
    queryKey: ["lessonPlans"],
    queryFn: () => teacherApi.getLessonPlans(),
    retry: 1,
  });

  // Mutations
  const createPlanMutation = useMutation({
    mutationFn: teacherApi.createLessonPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessonPlans"] });
      toast({ title: "✨ Lesson plan created successfully" });
      setPlanDialog(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const generatePlanMutation = useMutation({
    mutationFn: teacherApi.generateLessonPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessonPlans"] });
      toast({ title: "🎉 AI generated your lesson plan!" });
      setAIDialog(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const updatePlanMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => teacherApi.updateLessonPlan(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessonPlans"] });
      toast({ title: "✅ Lesson plan updated" });
      setEditDialog(false);
      setSelectedPlan(null);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const deletePlanMutation = useMutation({
    mutationFn: teacherApi.deleteLessonPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessonPlans"] });
      toast({ title: "🗑️ Lesson plan deleted" });
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const handleCreatePlan = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      subject_id: formData.get("subject_id") as string,
      topic: formData.get("topic") as string,
      objectives: (formData.get("objectives") as string).split("\n").filter(Boolean),
      activities: (formData.get("activities") as string).split("\n").filter(Boolean),
      resources: (formData.get("resources") as string).split("\n").filter(Boolean),
      scheduled_date: formData.get("scheduled_date") as string,
    };
    createPlanMutation.mutate(data);
  };

  const handleAIGenerate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      subject: formData.get("subject") as string,
      topic: formData.get("topic") as string,
      grade: parseInt(formData.get("grade") as string),
    };
    generatePlanMutation.mutate(data);
  };

  const handleUpdatePlan = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedPlan) return;
    
    const formData = new FormData(e.currentTarget);
    const data = {
      topic: formData.get("topic") as string,
      objectives: (formData.get("objectives") as string).split("\n").filter(Boolean),
      activities: (formData.get("activities") as string).split("\n").filter(Boolean),
      resources: (formData.get("resources") as string).split("\n").filter(Boolean),
    };
    updatePlanMutation.mutate({ id: selectedPlan.id, data });
  };

  const handleViewPlan = (plan: any) => {
    setSelectedPlan(plan);
    setViewDialog(true);
  };

  const handleEditPlan = (plan: any) => {
    setSelectedPlan(plan);
    setEditDialog(true);
  };

  const handleDeletePlan = (planId: string) => {
    if (confirm("Are you sure you want to delete this lesson plan?")) {
      deletePlanMutation.mutate(planId);
    }
  };

  const filteredPlans = lessonPlans.filter((plan: any) =>
    plan.topic?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Stats calculations
  const stats = {
    total: lessonPlans.length,
    thisWeek: lessonPlans.filter((p: any) => {
      const date = new Date(p.scheduled_date);
      const now = new Date();
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return date >= weekAgo && date <= now;
    }).length,
    upcoming: lessonPlans.filter((p: any) => new Date(p.scheduled_date) > new Date()).length,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-blue-950 dark:to-indigo-950">
      <div className="container py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Hero Header with Gradient */}
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-8 text-white shadow-2xl">
            <div className="absolute inset-0 bg-grid-white/10"></div>
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
                      <BookOpen className="h-8 w-8" />
                    </div>
                    <div>
                      <h1 className="text-4xl font-bold tracking-tight">Lesson Plans</h1>
                      <p className="text-blue-100 mt-1">AI-powered teaching excellence</p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button
                    size="lg"
                    variant="secondary"
                    className="bg-white/20 hover:bg-white/30 backdrop-blur-sm border-white/30 text-white shadow-lg"
                    onClick={() => setAIDialog(true)}
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    AI Generate
                  </Button>
                  <Button
                    size="lg"
                    className="bg-white text-blue-600 hover:bg-blue-50 shadow-lg"
                    onClick={() => setPlanDialog(true)}
                  >
                    <Plus className="h-5 w-5 mr-2" />
                    Create Plan
                  </Button>
                </div>
              </motion.div>

              {/* Stats Cards */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="grid grid-cols-3 gap-4 mt-6"
              >
                <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-white/20 p-2">
                      <Target className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{stats.total}</div>
                      <div className="text-sm text-blue-100">Total Plans</div>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-white/20 p-2">
                      <TrendingUp className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{stats.thisWeek}</div>
                      <div className="text-sm text-blue-100">This Week</div>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl bg-white/10 backdrop-blur-sm p-4 border border-white/20">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-white/20 p-2">
                      <Calendar className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold">{stats.upcoming}</div>
                      <div className="text-sm text-blue-100">Upcoming</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="relative max-w-2xl"
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search lesson plans by topic..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-14 text-lg rounded-2xl border-2 shadow-sm"
            />
          </motion.div>

          {/* Lesson Plans Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="border-2 shadow-xl rounded-2xl overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-900 dark:to-blue-900 border-b-2">
                <CardTitle className="text-2xl">My Lesson Plans</CardTitle>
                <CardDescription className="text-base">Manage all your teaching plans in one place</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-20">
                    <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                    <p className="text-muted-foreground">Loading your lesson plans...</p>
                  </div>
                ) : filteredPlans.length === 0 ? (
                  <div className="text-center py-20">
                    <div className="rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900 dark:to-indigo-900 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                      <BookOpen className="h-12 w-12 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-semibold mb-2">No lesson plans yet</h3>
                    <p className="text-muted-foreground mb-6">Create your first lesson plan or let AI generate one for you!</p>
                    <div className="flex gap-3 justify-center">
                      <Button onClick={() => setAIDialog(true)} size="lg">
                        <Sparkles className="h-5 w-5 mr-2" />
                        AI Generate
                      </Button>
                      <Button onClick={() => setPlanDialog(true)} variant="outline" size="lg">
                        <Plus className="h-5 w-5 mr-2" />
                        Create Manually
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <AnimatePresence>
                      {filteredPlans.map((plan: any, index: number) => (
                        <motion.div
                          key={plan.id}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.9 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <Card className="group hover:shadow-2xl transition-all duration-300 border-2 hover:border-primary/50 rounded-xl overflow-hidden">
                            <div className="h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between">
                                <CardTitle className="text-lg line-clamp-2 group-hover:text-primary transition-colors">
                                  {plan.topic}
                                </CardTitle>
                                <Badge variant="secondary" className="shrink-0">
                                  {plan.status || "Draft"}
                                </Badge>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="space-y-2 text-sm">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                  <Calendar className="h-4 w-4" />
                                  <span>{new Date(plan.scheduled_date).toLocaleDateString()}</span>
                                </div>
                                <div className="flex items-center gap-2 text-muted-foreground">
                                  <Target className="h-4 w-4" />
                                  <span>{plan.objectives?.length || 0} objectives</span>
                                </div>
                              </div>
                              
                              <div className="flex gap-2 pt-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="flex-1"
                                  onClick={() => handleViewPlan(plan)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  View
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEditPlan(plan)}
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-destructive hover:bg-destructive hover:text-white"
                                  onClick={() => handleDeletePlan(plan.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
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

        {/* AI Generate Dialog */}
        <Dialog open={aiDialog} onOpenChange={setAIDialog}>
          <DialogContent className="sm:max-w-[600px] rounded-2xl">
            <DialogHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 p-3">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div>
                  <DialogTitle className="text-2xl">AI Lesson Plan Generator</DialogTitle>
                  <DialogDescription className="text-base">Let AI create a comprehensive lesson plan for you</DialogDescription>
                </div>
              </div>
            </DialogHeader>
            <form onSubmit={handleAIGenerate} className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="subject" className="text-base font-medium">Subject</Label>
                  <Input
                    id="subject"
                    name="subject"
                    placeholder="e.g., Mathematics"
                    required
                    className="mt-2 h-12"
                  />
                </div>
                <div>
                  <Label htmlFor="topic" className="text-base font-medium">Topic</Label>
                  <Input
                    id="topic"
                    name="topic"
                    placeholder="e.g., Quadratic Equations"
                    required
                    className="mt-2 h-12"
                  />
                </div>
                <div>
                  <Label htmlFor="grade" className="text-base font-medium">Grade Level</Label>
                  <Input
                    id="grade"
                    name="grade"
                    type="number"
                    placeholder="e.g., 10"
                    required
                    min="1"
                    max="12"
                    className="mt-2 h-12"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setAIDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={generatePlanMutation.isPending} className="bg-gradient-to-r from-blue-600 to-indigo-600">
                  {generatePlanMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Generate with AI
                    </>
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Create Plan Dialog */}
        <Dialog open={planDialog} onOpenChange={setPlanDialog}>
          <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl">Create Lesson Plan</DialogTitle>
              <DialogDescription className="text-base">Fill in the details to create a new lesson plan</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreatePlan} className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="subject_id">Subject ID</Label>
                  <Input id="subject_id" name="subject_id" required className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="topic">Topic</Label>
                  <Input id="topic" name="topic" required className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="objectives">Learning Objectives (one per line)</Label>
                  <Textarea id="objectives" name="objectives" rows={4} required className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="activities">Activities (one per line)</Label>
                  <Textarea id="activities" name="activities" rows={4} required className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="resources">Resources (one per line)</Label>
                  <Textarea id="resources" name="resources" rows={3} className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="scheduled_date">Scheduled Date</Label>
                  <Input id="scheduled_date" name="scheduled_date" type="date" required className="mt-2" />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setPlanDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createPlanMutation.isPending}>
                  {createPlanMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Plan"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* View Plan Dialog */}
        <Dialog open={viewDialog} onOpenChange={setViewDialog}>
          <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl">{selectedPlan?.topic}</DialogTitle>
              <DialogDescription>
                Scheduled for {selectedPlan?.scheduled_date && new Date(selectedPlan.scheduled_date).toLocaleDateString()}
              </DialogDescription>
            </DialogHeader>
            {selectedPlan && (
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                    <Target className="h-5 w-5 text-primary" />
                    Learning Objectives
                  </h4>
                  <ul className="space-y-2">
                    {selectedPlan.objectives?.map((obj: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <ChevronRight className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-lg mb-3 flex items-center gap-2">
                    <Award className="h-5 w-5 text-primary" />
                    Activities
                  </h4>
                  <ul className="space-y-2">
                    {selectedPlan.activities?.map((activity: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <ChevronRight className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span>{activity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                {selectedPlan.resources && selectedPlan.resources.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-lg mb-3">Resources</h4>
                    <ul className="space-y-2">
                      {selectedPlan.resources.map((resource: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <ChevronRight className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                          <span>{resource}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            <DialogFooter>
              <Button onClick={() => setViewDialog(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Plan Dialog */}
        <Dialog open={editDialog} onOpenChange={setEditDialog}>
          <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl">Edit Lesson Plan</DialogTitle>
              <DialogDescription>Update your lesson plan details</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleUpdatePlan} className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="edit-topic">Topic</Label>
                  <Input
                    id="edit-topic"
                    name="topic"
                    defaultValue={selectedPlan?.topic}
                    required
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-objectives">Learning Objectives (one per line)</Label>
                  <Textarea
                    id="edit-objectives"
                    name="objectives"
                    defaultValue={selectedPlan?.objectives?.join("\n")}
                    rows={4}
                    required
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-activities">Activities (one per line)</Label>
                  <Textarea
                    id="edit-activities"
                    name="activities"
                    defaultValue={selectedPlan?.activities?.join("\n")}
                    rows={4}
                    required
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-resources">Resources (one per line)</Label>
                  <Textarea
                    id="edit-resources"
                    name="resources"
                    defaultValue={selectedPlan?.resources?.join("\n")}
                    rows={3}
                    className="mt-2"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setEditDialog(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updatePlanMutation.isPending}>
                  {updatePlanMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Update Plan"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default LessonPlansPage;