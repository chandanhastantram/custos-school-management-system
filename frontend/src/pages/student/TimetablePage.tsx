import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

const TimetablePage = () => {
  const schedule = [
    { day: "Monday", periods: [
      { time: "08:00 - 09:00", subject: "Mathematics", teacher: "Mr. Wilson", room: "101" },
      { time: "09:00 - 10:00", subject: "Physics", teacher: "Dr. Brown", room: "Lab 1" },
      { time: "10:00 - 11:00", subject: "English", teacher: "Ms. Johnson", room: "205" },
    ]},
    { day: "Tuesday", periods: [
      { time: "08:00 - 09:00", subject: "Chemistry", teacher: "Dr. Smith", room: "Lab 2" },
      { time: "09:00 - 10:00", subject: "History", teacher: "Mr. Davis", room: "302" },
    ]},
  ];

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Calendar className="h-8 w-8 text-primary" />
            My Timetable
          </h1>
          <p className="text-muted-foreground mt-1">View your weekly class schedule</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Today's Classes</CardDescription>
              <CardTitle className="text-3xl">6</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Week</CardDescription>
              <CardTitle className="text-3xl">30</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Next Class</CardDescription>
              <CardTitle className="text-lg flex items-center gap-1">
                <Clock className="h-4 w-4" />
                in 45 min
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Attendance</CardDescription>
              <CardTitle className="text-3xl">95%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="week" className="space-y-4">
          <TabsList>
            <TabsTrigger value="week">Week View</TabsTrigger>
            <TabsTrigger value="day">Day View</TabsTrigger>
          </TabsList>

          <TabsContent value="week">
            <div className="space-y-4">
              {schedule.map((day) => (
                <Card key={day.day}>
                  <CardHeader>
                    <CardTitle className="text-lg">{day.day}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {day.periods.map((period, idx) => (
                        <div key={idx} className="flex items-center gap-4 p-4 border rounded-lg">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground min-w-[120px]">
                            <Clock className="h-4 w-4" />
                            {period.time}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold">{period.subject}</h4>
                            <p className="text-sm text-muted-foreground">{period.teacher} • Room {period.room}</p>
                          </div>
                          <Badge variant="outline">{period.room}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="day">
            <Card>
              <CardHeader>
                <CardTitle>Today's Schedule</CardTitle>
                <CardDescription>Monday, February 13, 2024</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Day view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default TimetablePage;
