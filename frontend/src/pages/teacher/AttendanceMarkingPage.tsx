import { useState } from "react";
import { motion } from "framer-motion";
import { ClipboardCheck, Calendar, Users, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

const AttendanceMarkingPage = () => {
  const [selectedDate, setSelectedDate] = useState("2024-02-13");
  
  const classes = [
    { id: 1, name: "Mathematics - 10A", time: "09:00 AM", students: 30, marked: false },
    { id: 2, name: "Physics - 10B", time: "11:00 AM", students: 28, marked: true },
  ];

  const students = [
    { id: 1, name: "John Doe", rollNo: "10A-001", present: true },
    { id: 2, name: "Jane Smith", rollNo: "10A-002", present: true },
    { id: 3, name: "Alex Chen", rollNo: "10A-003", present: false },
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
              Mark Attendance
            </h1>
            <p className="text-muted-foreground mt-1">Record student attendance for your classes</p>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span className="font-medium">{selectedDate}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Today's Classes</CardDescription>
              <CardTitle className="text-3xl">4</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Marked</CardDescription>
              <CardTitle className="text-3xl text-green-600">2</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Pending</CardDescription>
              <CardTitle className="text-3xl text-orange-600">2</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg. Attendance</CardDescription>
              <CardTitle className="text-3xl">92%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="today" className="space-y-4">
          <TabsList>
            <TabsTrigger value="today">Today's Classes</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="today">
            <div className="space-y-4">
              {classes.map((classItem) => (
                <Card key={classItem.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{classItem.name}</CardTitle>
                        <CardDescription className="flex items-center gap-4 mt-1">
                          <span>{classItem.time}</span>
                          <span className="flex items-center gap-1">
                            <Users className="h-4 w-4" />
                            {classItem.students} students
                          </span>
                        </CardDescription>
                      </div>
                      {classItem.marked ? (
                        <Badge variant="default" className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" />
                          Marked
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Pending</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {!classItem.marked ? (
                      <Button className="w-full">Mark Attendance</Button>
                    ) : (
                      <div className="flex gap-2">
                        <Button variant="outline" className="flex-1">View</Button>
                        <Button variant="outline" className="flex-1">Edit</Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Attendance History</CardTitle>
                <CardDescription>Past attendance records</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">History view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Quick Mark Modal (simplified) */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle>Quick Mark - Mathematics 10A</CardTitle>
            <CardDescription>Mark all present, then uncheck absent students</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {students.map((student) => (
                <div key={student.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Checkbox checked={student.present} />
                    <div>
                      <p className="font-medium">{student.name}</p>
                      <p className="text-sm text-muted-foreground">{student.rollNo}</p>
                    </div>
                  </div>
                  {student.present ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
              ))}
              <div className="flex gap-2 mt-4">
                <Button variant="outline" className="flex-1">Mark All Present</Button>
                <Button className="flex-1">Submit Attendance</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default AttendanceMarkingPage;
