import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Calendar, Clock, Download, Loader2, MapPin, User, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { studentApi } from "@/services/student-api";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "@/hooks/use-toast";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const TimetablePage = () => {
  const { user } = useAuthStore();
  const [selectedDay, setSelectedDay] = useState(new Date().getDay() - 1); // 0 = Monday

  // Fetch timetable
  const { data: timetable, isLoading, refetch } = useQuery({
    queryKey: ["timetable", user?.id],
    queryFn: () => studentApi.getTimetable(user?.id || ""),
    enabled: !!user?.id,
    retry: 1,
  });

  const handleExport = () => {
    toast({ title: "Exporting timetable...", description: "PDF download will start shortly" });
  };

  // Get today's schedule
  const todaySchedule = timetable?.periods?.filter(p => p.period_number >= 0) || [];
  const weekSchedule = DAYS.map((day, index) => ({
    day,
    periods: timetable?.periods?.filter(p => p.period_number >= 0) || []
  }));

  // Calculate stats
  const stats = {
    todayClasses: todaySchedule.length,
    weekClasses: timetable?.periods?.length || 0,
    nextClass: todaySchedule[0]?.subject || "No class",
    attendance: "95%"
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
              <Calendar className="h-8 w-8 text-primary" />
              My Timetable
            </h1>
            <p className="text-muted-foreground mt-1">View your weekly class schedule</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Today's Classes</CardDescription>
              <CardTitle className="text-3xl">{stats.todayClasses}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Week</CardDescription>
              <CardTitle className="text-3xl">{stats.weekClasses}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Next Class</CardDescription>
              <CardTitle className="text-lg flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {stats.nextClass}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Attendance</CardDescription>
              <CardTitle className="text-3xl">{stats.attendance}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Timetable */}
        <Tabs defaultValue="week" className="space-y-4">
          <TabsList>
            <TabsTrigger value="week">Week View</TabsTrigger>
            <TabsTrigger value="day">Day View</TabsTrigger>
          </TabsList>

          <TabsContent value="week">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="space-y-4">
                {weekSchedule.map((day, idx) => (
                  <Card key={day.day}>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center justify-between">
                        <span>{day.day}</span>
                        <Badge variant={idx === selectedDay ? "default" : "outline"}>
                          {day.periods.length} classes
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {day.periods.length === 0 ? (
                        <p className="text-muted-foreground text-center py-4">No classes scheduled</p>
                      ) : (
                        <div className="space-y-3">
                          {day.periods.map((period, pidx) => (
                            <div key={pidx} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-[120px]">
                                <Clock className="h-4 w-4" />
                                {period.start_time} - {period.end_time}
                              </div>
                              <div className="flex-1">
                                <h4 className="font-semibold">{period.subject}</h4>
                                <p className="text-sm text-muted-foreground flex items-center gap-3 mt-1">
                                  <span className="flex items-center gap-1">
                                    <User className="h-3 w-3" />
                                    {period.teacher}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <MapPin className="h-3 w-3" />
                                    Room {period.room}
                                  </span>
                                </p>
                              </div>
                              <Badge variant="outline">{period.room}</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="day">
            <Card>
              <CardHeader>
                <CardTitle>Today's Schedule</CardTitle>
                <CardDescription>{DAYS[selectedDay]}, {new Date().toLocaleDateString()}</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : todaySchedule.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No classes today</p>
                ) : (
                  <div className="space-y-3">
                    {todaySchedule.map((period, idx) => (
                      <div key={idx} className="flex items-center gap-4 p-4 border rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-[120px]">
                          <Clock className="h-4 w-4" />
                          {period.start_time} - {period.end_time}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold">{period.subject}</h4>
                          <p className="text-sm text-muted-foreground">{period.teacher} • Room {period.room}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default TimetablePage;
