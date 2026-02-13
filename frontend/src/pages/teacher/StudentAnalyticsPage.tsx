import { useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, TrendingDown, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";

const StudentAnalyticsPage = () => {
  const classStats = {
    avgScore: 78,
    attendance: 92,
    topPerformers: 5,
    needsAttention: 3
  };

  const students = [
    { 
      id: 1, 
      name: "John Doe", 
      rollNo: "10A-001", 
      avgScore: 85, 
      attendance: 95, 
      trend: "up",
      assignments: { completed: 18, total: 20 }
    },
    { 
      id: 2, 
      name: "Jane Smith", 
      rollNo: "10A-002", 
      avgScore: 72, 
      attendance: 88, 
      trend: "down",
      assignments: { completed: 15, total: 20 }
    },
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
              <BarChart3 className="h-8 w-8 text-primary" />
              Student Analytics
            </h1>
            <p className="text-muted-foreground mt-1">Track student performance and engagement</p>
          </div>
          <Button variant="outline">Export Report</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Class Average</CardDescription>
              <CardTitle className="text-3xl">{classStats.avgScore}%</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg. Attendance</CardDescription>
              <CardTitle className="text-3xl">{classStats.attendance}%</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Top Performers</CardDescription>
              <CardTitle className="text-3xl text-green-600">{classStats.topPerformers}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Needs Attention</CardDescription>
              <CardTitle className="text-3xl text-orange-600">{classStats.needsAttention}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="attendance">Attendance</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle>Student Performance Overview</CardTitle>
                <CardDescription>Individual student metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {students.map((student) => (
                    <Card key={student.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <Avatar className="h-12 w-12">
                              <AvatarFallback>{student.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                            </Avatar>
                            <div>
                              <h4 className="font-semibold">{student.name}</h4>
                              <p className="text-sm text-muted-foreground">{student.rollNo}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {student.trend === "up" ? (
                              <TrendingUp className="h-5 w-5 text-green-500" />
                            ) : (
                              <TrendingDown className="h-5 w-5 text-red-500" />
                            )}
                            <Badge variant={student.avgScore >= 75 ? "default" : "secondary"}>
                              {student.avgScore}%
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground mb-1">Average Score</p>
                            <Progress value={student.avgScore} className="h-2" />
                            <p className="text-sm font-medium mt-1">{student.avgScore}%</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground mb-1">Attendance</p>
                            <Progress value={student.attendance} className="h-2" />
                            <p className="text-sm font-medium mt-1">{student.attendance}%</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground mb-1">Assignments</p>
                            <Progress value={(student.assignments.completed / student.assignments.total) * 100} className="h-2" />
                            <p className="text-sm font-medium mt-1">
                              {student.assignments.completed}/{student.assignments.total}
                            </p>
                          </div>
                        </div>
                        <Button variant="outline" size="sm" className="w-full mt-4">
                          View Detailed Report
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="performance">
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Performance charts coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="attendance">
            <Card>
              <CardHeader>
                <CardTitle>Attendance Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Attendance analytics coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default StudentAnalyticsPage;
