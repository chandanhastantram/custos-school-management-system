import { useState } from "react";
import { motion } from "framer-motion";
import { ClipboardCheck, Calendar, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";

const ParentChildAttendancePage = () => {
  const [selectedChild, setSelectedChild] = useState("1");

  const children = [
    { id: "1", name: "John Doe", class: "10-A" },
    { id: "2", name: "Jane Doe", class: "8-B" },
  ];

  const attendanceStats = {
    overall: 92,
    thisMonth: 95,
    present: 165,
    absent: 15,
    totalDays: 180
  };

  const recentAttendance = [
    { date: "2024-02-13", status: "Present", classes: 6 },
    { date: "2024-02-12", status: "Present", classes: 6 },
    { date: "2024-02-11", status: "Absent", classes: 0 },
    { date: "2024-02-10", status: "Present", classes: 5 },
  ];

  const monthlyData = [
    { month: "January", percentage: 94 },
    { month: "February", percentage: 95 },
    { month: "December", percentage: 90 },
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
              <ClipboardCheck className="h-8 w-8 text-primary" />
              Child&apos;s Attendance
            </h1>
            <p className="text-muted-foreground mt-1">Monitor your child&apos;s attendance records</p>
          </div>
          <Select value={selectedChild} onValueChange={setSelectedChild}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select child" />
            </SelectTrigger>
            <SelectContent>
              {children.map((child) => (
                <SelectItem key={child.id} value={child.id}>
                  {child.name} - Class {child.class}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

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

        <Tabs defaultValue="recent" className="space-y-4">
          <TabsList>
            <TabsTrigger value="recent">Recent Attendance</TabsTrigger>
            <TabsTrigger value="monthly">Monthly Trends</TabsTrigger>
          </TabsList>

          <TabsContent value="recent">
            <Card>
              <CardHeader>
                <CardTitle>Recent Attendance</CardTitle>
                <CardDescription>Last 30 days attendance record</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentAttendance.map((record, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Calendar className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{record.date}</p>
                          <p className="text-sm text-muted-foreground">
                            {record.classes} classes
                          </p>
                        </div>
                      </div>
                      <Badge variant={record.status === "Present" ? "default" : "destructive"}>
                        {record.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monthly">
            <Card>
              <CardHeader>
                <CardTitle>Monthly Attendance Trends</CardTitle>
                <CardDescription>Month-wise attendance percentage</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {monthlyData.map((month, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{month.month}</span>
                        <span className="text-sm font-semibold">{month.percentage}%</span>
                      </div>
                      <Progress value={month.percentage} className="h-2" />
                    </div>
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

export default ParentChildAttendancePage;
