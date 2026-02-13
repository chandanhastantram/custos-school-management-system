import { useState } from "react";
import { motion } from "framer-motion";
import { Video, Calendar, Users, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

const VirtualClassroomPage = () => {
  const upcomingClasses = [
    { id: 1, subject: "Mathematics", teacher: "Mr. Wilson", time: "10:00 AM", duration: "45 min", link: "join-123" },
    { id: 2, subject: "Physics", teacher: "Dr. Brown", time: "02:00 PM", duration: "60 min", link: "join-456" },
  ];

  const recordings = [
    { id: 1, subject: "Chemistry", topic: "Organic Compounds", date: "2024-02-12", duration: "50 min", views: 45 },
    { id: 2, subject: "Biology", topic: "Cell Division", date: "2024-02-10", duration: "45 min", views: 38 },
  ];

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Video className="h-8 w-8 text-primary" />
              Virtual Classroom
            </h1>
            <p className="text-muted-foreground mt-1">Join live classes and watch recordings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Today&apos;s Classes</CardDescription>
              <CardTitle className="text-3xl">3</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Next Class</CardDescription>
              <CardTitle className="text-lg">in 30 min</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Recordings</CardDescription>
              <CardTitle className="text-3xl">45</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Attendance</CardDescription>
              <CardTitle className="text-3xl">95%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="upcoming" className="space-y-4">
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming Classes</TabsTrigger>
            <TabsTrigger value="recordings">Recordings</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming">
            <Card>
              <CardHeader>
                <CardTitle>Today&apos;s Live Classes</CardTitle>
                <CardDescription>Join your scheduled online classes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {upcomingClasses.map((classItem) => (
                    <Card key={classItem.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{classItem.subject}</CardTitle>
                            <CardDescription className="flex items-center gap-4 mt-2">
                              <span>{classItem.teacher}</span>
                              <span className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {classItem.time}
                              </span>
                              <span>{classItem.duration}</span>
                            </CardDescription>
                          </div>
                          <Badge>Live</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <Button className="w-full">
                          <Video className="h-4 w-4 mr-2" />
                          Join Class
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recordings">
            <Card>
              <CardHeader>
                <CardTitle>Class Recordings</CardTitle>
                <CardDescription>Watch previous class recordings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recordings.map((recording) => (
                    <Card key={recording.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{recording.subject}</CardTitle>
                            <CardDescription className="mt-1">{recording.topic}</CardDescription>
                          </div>
                          <Badge variant="outline">Recorded</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>{recording.date}</span>
                            <span>{recording.duration}</span>
                            <span className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              {recording.views} views
                            </span>
                          </div>
                          <Button variant="outline" size="sm">
                            <Play className="h-4 w-4 mr-2" />
                            Watch
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default VirtualClassroomPage;
