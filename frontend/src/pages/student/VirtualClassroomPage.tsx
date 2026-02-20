import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Video, Calendar, Clock, Users, ExternalLink,
  Play, MonitorPlay, RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { studentApi } from "@/services/student-api";
import { cn } from "@/lib/utils";

// Demo data (fallback)
const DEMO_UPCOMING = [
  { id: "1", title: "Mathematics - Quadratic Equations", teacher: "Mr. Sharma", date: "2024-02-13", time: "10:00 AM", duration: "45 min", platform: "Zoom", link: "#", status: "scheduled" },
  { id: "2", title: "Physics - Newton's Laws", teacher: "Mrs. Verma", date: "2024-02-13", time: "11:30 AM", duration: "45 min", platform: "Google Meet", link: "#", status: "scheduled" },
  { id: "3", title: "English - Essay Writing", teacher: "Mr. Patel", date: "2024-02-14", time: "09:00 AM", duration: "40 min", platform: "Zoom", link: "#", status: "scheduled" },
];

const DEMO_RECORDINGS = [
  { id: "r1", title: "Chemistry - Periodic Table", teacher: "Mrs. Das", date: "2024-02-10", duration: "42 min", views: 28 },
  { id: "r2", title: "Mathematics - Trigonometry", teacher: "Mr. Sharma", date: "2024-02-09", duration: "45 min", views: 35 },
  { id: "r3", title: "Biology - Cell Structure", teacher: "Mr. Kumar", date: "2024-02-08", duration: "38 min", views: 22 },
];

const VirtualClassroomPage = () => {
  const [demoMode, setDemoMode] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["virtual-classes"],
    queryFn: () => studentApi.getUpcomingClasses(),
    retry: 1,
    staleTime: 30000,
  });

  useEffect(() => {
    if (isError && !demoMode) setDemoMode(true);
  }, [isError, demoMode]);

  const upcoming = demoMode ? DEMO_UPCOMING : (data?.upcoming || DEMO_UPCOMING);
  const recordings = demoMode ? DEMO_RECORDINGS : (data?.recordings || DEMO_RECORDINGS);

  const handleJoin = async (classId: string) => {
    if (demoMode) {
      window.open("#", "_blank");
      return;
    }
    try {
      const result = await studentApi.joinClass(classId);
      if (result?.link) window.open(result.link, "_blank");
    } catch {
      window.open("#", "_blank");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Virtual Classroom</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Join live classes and watch recordings</p>
        </div>
        {!demoMode && (
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
        )}
      </div>

      <Tabs defaultValue="upcoming" className="space-y-4">
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming Classes</TabsTrigger>
          <TabsTrigger value="recordings">Recordings</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="space-y-4">
          {upcoming.length === 0 ? (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <Video className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No upcoming classes scheduled</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {upcoming.map((cls: any, i: number) => (
                <motion.div
                  key={cls.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="hover:shadow-md transition-shadow h-full">
                    <CardContent className="p-5 flex flex-col h-full">
                      <div className="flex items-start justify-between mb-3">
                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Video className="h-5 w-5 text-primary" />
                        </div>
                        <Badge variant="secondary">{cls.platform}</Badge>
                      </div>
                      <h3 className="font-semibold text-sm mb-1">{cls.title}</h3>
                      <p className="text-xs text-muted-foreground mb-3">{cls.teacher}</p>
                      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mb-4">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" /> {cls.date}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {cls.time}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {cls.duration}
                        </span>
                      </div>
                      <div className="mt-auto">
                        <Button size="sm" className="w-full" onClick={() => handleJoin(cls.id)}>
                          <ExternalLink className="h-4 w-4 mr-1" /> Join Class
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="recordings" className="space-y-4">
          {recordings.length === 0 ? (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <MonitorPlay className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No recordings available</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {recordings.map((rec: any, i: number) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="hover:bg-muted/30 transition-colors">
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <Play className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm">{rec.title}</h3>
                        <p className="text-xs text-muted-foreground">{rec.teacher} · {rec.date}</p>
                      </div>
                      <div className="text-right text-xs text-muted-foreground shrink-0">
                        <p>{rec.duration}</p>
                        <p>{rec.views} views</p>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Play className="h-4 w-4 mr-1" /> Watch
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VirtualClassroomPage;
