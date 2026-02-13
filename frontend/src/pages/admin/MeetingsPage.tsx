import { useState } from "react";
import { motion } from "framer-motion";
import { Video, Plus, Calendar as CalendarIcon, Users, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const MeetingsPage = () => {
  const upcomingMeetings = [
    { id: 1, title: "Math Class - Grade 10A", host: "James Wilson", date: "2024-02-14", time: "10:00 AM", participants: 30, status: "Scheduled" },
    { id: 2, title: "Parent-Teacher Meeting", host: "Sarah Johnson", date: "2024-02-15", time: "02:00 PM", participants: 15, status: "Scheduled" },
  ];

  const pastMeetings = [
    { id: 3, title: "Science Lab Session", host: "Emily Brown", date: "2024-02-12", time: "11:00 AM", duration: "45 min", recording: true },
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
              Virtual Meetings
            </h1>
            <p className="text-muted-foreground mt-1">Schedule and manage online classes and meetings</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Schedule Meeting
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Today's Meetings</CardDescription>
              <CardTitle className="text-3xl">5</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Week</CardDescription>
              <CardTitle className="text-3xl">24</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Participants</CardDescription>
              <CardTitle className="text-3xl">450</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Recordings</CardDescription>
              <CardTitle className="text-3xl">128</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="upcoming" className="space-y-4">
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="past">Past Meetings</TabsTrigger>
            <TabsTrigger value="recordings">Recordings</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming">
            <Card>
              <CardHeader>
                <CardTitle>Upcoming Meetings</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Host</TableHead>
                      <TableHead>Date & Time</TableHead>
                      <TableHead>Participants</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {upcomingMeetings.map((meeting) => (
                      <TableRow key={meeting.id}>
                        <TableCell className="font-medium">{meeting.title}</TableCell>
                        <TableCell>{meeting.host}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                            {meeting.date} {meeting.time}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {meeting.participants}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge>{meeting.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button size="sm">Join</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="past">
            <Card>
              <CardHeader>
                <CardTitle>Past Meetings</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Host</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Recording</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pastMeetings.map((meeting) => (
                      <TableRow key={meeting.id}>
                        <TableCell className="font-medium">{meeting.title}</TableCell>
                        <TableCell>{meeting.host}</TableCell>
                        <TableCell>{meeting.date} {meeting.time}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {meeting.duration}
                          </div>
                        </TableCell>
                        <TableCell>
                          {meeting.recording && <Badge variant="outline">Available</Badge>}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recordings">
            <Card>
              <CardHeader>
                <CardTitle>Meeting Recordings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Recording library coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default MeetingsPage;
