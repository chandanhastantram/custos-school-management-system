import { useState } from "react";
import { motion } from "framer-motion";
import { Users, DollarSign, Calendar, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const ParentDashboard = () => {
  const [selectedChild, setSelectedChild] = useState("1");

  const children = [
    { id: "1", name: "John Doe", class: "10-A", rollNo: "10A-001" },
    { id: "2", name: "Jane Doe", class: "8-B", rollNo: "8B-015" },
  ];

  const selectedChildData = children.find(c => c.id === selectedChild);

  const stats = {
    attendance: 92,
    avgGrade: 85,
    pendingFees: "$500",
    upcomingEvents: 3
  };

  const recentActivities = [
    { id: 1, type: "Grade", subject: "Mathematics", detail: "Scored 88%", date: "2024-02-12" },
    { id: 2, type: "Attendance", detail: "Marked present", date: "2024-02-13" },
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
              <Users className="h-8 w-8 text-primary" />
              Parent Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">Monitor your child&apos;s progress</p>
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

        {selectedChildData && (
          <>
            <Card className="border-2 border-primary">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarFallback className="text-xl">
                      {selectedChildData.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-2xl">{selectedChildData.name}</CardTitle>
                    <CardDescription className="text-base">
                      Class {selectedChildData.class} • Roll No: {selectedChildData.rollNo}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Attendance</CardDescription>
                  <CardTitle className="text-3xl">{stats.attendance}%</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Average Grade</CardDescription>
                  <CardTitle className="text-3xl">{stats.avgGrade}%</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Pending Fees</CardDescription>
                  <CardTitle className="text-3xl text-destructive">{stats.pendingFees}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardDescription>Upcoming Events</CardDescription>
                  <CardTitle className="text-3xl">{stats.upcomingEvents}</CardTitle>
                </CardHeader>
              </Card>
            </div>

            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="academics">Academics</TabsTrigger>
                <TabsTrigger value="attendance">Attendance</TabsTrigger>
                <TabsTrigger value="fees">Fees</TabsTrigger>
              </TabsList>

              <TabsContent value="overview">
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Activities</CardTitle>
                    <CardDescription>Latest updates about your child</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {recentActivities.map((activity) => (
                        <div key={activity.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{activity.type}</Badge>
                              {activity.subject && <span className="font-medium">{activity.subject}</span>}
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">{activity.detail}</p>
                          </div>
                          <span className="text-sm text-muted-foreground">{activity.date}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="academics">
                <Card>
                  <CardHeader>
                    <CardTitle>Academic Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">Academic details coming soon...</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="attendance">
                <Card>
                  <CardHeader>
                    <CardTitle>Attendance Records</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">Attendance details coming soon...</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="fees">
                <Card>
                  <CardHeader>
                    <CardTitle>Fee Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground">Fee details coming soon...</p>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default ParentDashboard;
