import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar, TrendingUp, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const StudentAttendancePage = () => {
  const attendanceStats = {
    overall: 88,
    thisMonth: 92,
    present: 158,
    absent: 22,
    totalDays: 180,
    lowAttendanceSubjects: ["Physics", "Chemistry"]
  };

  const subjectWise = [
    { subject: "Mathematics", percentage: 95, present: 38, total: 40 },
    { subject: "Physics", percentage: 75, present: 30, total: 40 },
    { subject: "Chemistry", percentage: 80, present: 32, total: 40 },
    { subject: "English", percentage: 92, present: 37, total: 40 },
  ];

  const recentAttendance = [
    { date: "2024-02-13", day: "Tuesday", status: "Present", classes: 6 },
    { date: "2024-02-12", day: "Monday", status: "Present", classes: 6 },
    { date: "2024-02-11", day: "Sunday", status: "Holiday", classes: 0 },
    { date: "2024-02-10", day: "Saturday", status: "Absent", classes: 0 },
    { date: "2024-02-09", day: "Friday", status: "Present", classes: 5 },
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
              <Calendar className="h-8 w-8 text-primary" />
              My Attendance
            </h1>
            <p className="text-muted-foreground mt-1">Track your attendance records</p>
          </div>
        </div>

        {attendanceStats.overall < 75 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Low Attendance Warning</AlertTitle>
            <AlertDescription>
              Your overall attendance is {attendanceStats.overall}%. Minimum 75% required. 
              Low in: {attendanceStats.lowAttendanceSubjects.join(", ")}
            </AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Overall Attendance</CardDescription>
              <CardTitle className="text-3xl">{attendanceStats.overall}%</CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={attendanceStats.overall} className="h-2" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Month</CardDescription>
              <CardTitle className="text-3xl flex items-center gap-1">
                {attendanceStats.thisMonth}%
                <TrendingUp className="h-5 w-5 text-green-500" />
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Days Present</CardDescription>
              <CardTitle className="text-3xl text-green-600">{attendanceStats.present}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Days Absent</CardDescription>
              <CardTitle className="text-3xl text-red-600">{attendanceStats.absent}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="subject" className="space-y-4">
          <TabsList>
            <TabsTrigger value="subject">Subject-wise</TabsTrigger>
            <TabsTrigger value="recent">Recent Records</TabsTrigger>
            <TabsTrigger value="calendar">Calendar View</TabsTrigger>
          </TabsList>

          <TabsContent value="subject">
            <Card>
              <CardHeader>
                <CardTitle>Subject-wise Attendance</CardTitle>
                <CardDescription>Attendance breakdown by subject</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {subjectWise.map((subject) => (
                    <div key={subject.subject} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{subject.subject}</span>
                          {subject.percentage < 75 && (
                            <Badge variant="destructive" className="text-xs">Low</Badge>
                          )}
                        </div>
                        <span className="text-sm font-semibold">
                          {subject.percentage}% ({subject.present}/{subject.total})
                        </span>
                      </div>
                      <Progress 
                        value={subject.percentage} 
                        className={`h-2 ${subject.percentage < 75 ? 'bg-red-100' : ''}`}
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recent">
            <Card>
              <CardHeader>
                <CardTitle>Recent Attendance</CardTitle>
                <CardDescription>Last 30 days attendance records</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentAttendance.map((record, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Calendar className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{record.date}</p>
                          <p className="text-sm text-muted-foreground">{record.day}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground">
                          {record.classes} classes
                        </span>
                        <Badge variant={
                          record.status === "Present" ? "default" : 
                          record.status === "Holiday" ? "secondary" : 
                          "destructive"
                        }>
                          {record.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="calendar">
            <Card>
              <CardHeader>
                <CardTitle>Calendar View</CardTitle>
                <CardDescription>Monthly attendance calendar</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                  <p className="text-muted-foreground">Calendar view coming soon...</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default StudentAttendancePage;
