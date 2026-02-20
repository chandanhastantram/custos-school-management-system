import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Trophy, Star, Users, Calendar, MapPin, Clock,
  Plus, CheckCircle2, RefreshCw, Activity,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { studentApi } from "@/services/student-api";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// Demo data (fallback)
const DEMO_MY_ACTIVITIES = [
  { id: "a1", name: "Basketball Team", category: "Sports", role: "Player", schedule: "Mon, Wed, Fri - 4:00 PM", points: 120 },
  { id: "a2", name: "Science Club", category: "Academic", role: "Member", schedule: "Tue - 3:30 PM", points: 85 },
  { id: "a3", name: "Music Band", category: "Arts", role: "Guitarist", schedule: "Thu - 4:00 PM", points: 60 },
];

const DEMO_AVAILABLE = [
  { id: "b1", name: "Debate Club", category: "Academic", description: "Develop public speaking and argumentation skills", members: 18, maxMembers: 25, schedule: "Wed - 3:30 PM" },
  { id: "b2", name: "Chess Club", category: "Games", description: "Learn strategy and compete in tournaments", members: 12, maxMembers: 20, schedule: "Fri - 3:00 PM" },
  { id: "b3", name: "Art Workshop", category: "Arts", description: "Express creativity through painting and sculpture", members: 22, maxMembers: 30, schedule: "Sat - 10:00 AM" },
];

const DEMO_ACHIEVEMENTS = [
  { id: "c1", title: "Basketball District Champions", date: "2024-01-15", category: "Sports", points: 50 },
  { id: "c2", title: "Science Fair - 2nd Place", date: "2024-01-20", category: "Academic", points: 40 },
  { id: "c3", title: "Music Performance - Annual Day", date: "2023-12-10", category: "Arts", points: 30 },
];

const CATEGORY_COLORS: Record<string, string> = {
  Sports: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  Academic: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  Arts: "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300",
  Games: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
};

const ExtracurricularPage = () => {
  const queryClient = useQueryClient();
  const [demoMode, setDemoMode] = useState(false);
  const [demoAvailable, setDemoAvailable] = useState(DEMO_AVAILABLE);

  const { data, isError, refetch } = useQuery({
    queryKey: ["student-activities"],
    queryFn: () => studentApi.getActivities(),
    retry: 1,
    staleTime: 30000,
  });

  useEffect(() => {
    if (isError && !demoMode) setDemoMode(true);
  }, [isError, demoMode]);

  const enrollMutation = useMutation({
    mutationFn: (activityId: string) => studentApi.enrollActivity(activityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-activities"] });
      toast({ title: "Enrolled!", description: "You have been enrolled in the activity." });
    },
    onError: () => {
      toast({ title: "Error", description: "Failed to enroll", variant: "destructive" });
    },
  });

  const handleEnroll = (activityId: string) => {
    if (demoMode) {
      setDemoAvailable(prev => prev.filter(a => a.id !== activityId));
      toast({ title: "Enrolled!", description: "You have been enrolled in the activity." });
      return;
    }
    enrollMutation.mutate(activityId);
  };

  const myActivities = demoMode ? DEMO_MY_ACTIVITIES : (data?.my_activities || DEMO_MY_ACTIVITIES);
  const available = demoMode ? demoAvailable : (data?.available || DEMO_AVAILABLE);
  const achievements = demoMode ? DEMO_ACHIEVEMENTS : (data?.achievements || DEMO_ACHIEVEMENTS);
  const totalPoints = myActivities.reduce((sum: number, a: any) => sum + (a.points || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Extracurricular Activities</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Manage your activities and achievements</p>
        </div>
        {!demoMode && (
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "My Activities", value: myActivities.length, icon: Activity, color: "text-blue-600" },
          { label: "Total Points", value: totalPoints, icon: Star, color: "text-amber-600" },
          { label: "Achievements", value: achievements.length, icon: Trophy, color: "text-purple-600" },
          { label: "Available", value: available.length, icon: Plus, color: "text-emerald-600" },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", stat.color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
                <stat.icon className={cn("h-5 w-5", stat.color)} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className={cn("text-lg font-bold", stat.color)}>{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="my" className="space-y-4">
        <TabsList>
          <TabsTrigger value="my">My Activities</TabsTrigger>
          <TabsTrigger value="available">Available</TabsTrigger>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
        </TabsList>

        {/* My Activities */}
        <TabsContent value="my" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {myActivities.map((activity: any, i: number) => (
              <motion.div key={activity.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Card className="h-full">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <Badge className={CATEGORY_COLORS[activity.category] || CATEGORY_COLORS.Sports}>
                        {activity.category}
                      </Badge>
                      <div className="flex items-center gap-1 text-amber-600">
                        <Star className="h-4 w-4" />
                        <span className="text-sm font-bold">{activity.points}</span>
                      </div>
                    </div>
                    <h3 className="font-semibold">{activity.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">Role: {activity.role}</p>
                    <div className="flex items-center gap-1 mt-3 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{activity.schedule}</span>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Available */}
        <TabsContent value="available" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {available.map((activity: any, i: number) => (
              <motion.div key={activity.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <Card className="h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <Badge className={cn("self-start mb-3", CATEGORY_COLORS[activity.category] || CATEGORY_COLORS.Sports)}>
                      {activity.category}
                    </Badge>
                    <h3 className="font-semibold">{activity.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">{activity.description}</p>
                    <div className="flex flex-wrap gap-3 mt-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" /> {activity.members}/{activity.maxMembers}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" /> {activity.schedule}
                      </span>
                    </div>
                    <div className="mt-auto pt-4">
                      <Button size="sm" className="w-full" onClick={() => handleEnroll(activity.id)}>
                        <Plus className="h-4 w-4 mr-1" /> Enroll
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Achievements */}
        <TabsContent value="achievements" className="space-y-3">
          {achievements.map((ach: any, i: number) => (
            <motion.div key={ach.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
              <Card className="hover:bg-muted/30 transition-colors">
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center shrink-0">
                    <Trophy className="h-5 w-5 text-amber-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm">{ach.title}</h3>
                    <p className="text-xs text-muted-foreground">{ach.date}</p>
                  </div>
                  <Badge className={CATEGORY_COLORS[ach.category] || CATEGORY_COLORS.Sports}>
                    {ach.category}
                  </Badge>
                  <div className="flex items-center gap-1 text-amber-600 shrink-0">
                    <Star className="h-4 w-4" />
                    <span className="text-sm font-bold">+{ach.points}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExtracurricularPage;
