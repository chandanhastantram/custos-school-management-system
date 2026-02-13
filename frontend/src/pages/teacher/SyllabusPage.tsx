import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, CheckCircle2, Circle, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

const SyllabusPage = () => {
  const syllabusData = {
    subject: "Mathematics - Grade 10",
    totalTopics: 45,
    completedTopics: 28,
    inProgressTopics: 5,
    estimatedHours: 120,
    completedHours: 75,
    units: [
      {
        id: 1,
        name: "Algebra",
        topics: [
          { id: 1, name: "Linear Equations", status: "completed", hours: 8, lessonPlanId: 1 },
          { id: 2, name: "Quadratic Equations", status: "completed", hours: 10, lessonPlanId: 2 },
          { id: 3, name: "Polynomials", status: "in-progress", hours: 12, lessonPlanId: 3 },
          { id: 4, name: "Arithmetic Progressions", status: "pending", hours: 8, lessonPlanId: null },
        ]
      },
      {
        id: 2,
        name: "Geometry",
        topics: [
          { id: 5, name: "Triangles", status: "completed", hours: 10, lessonPlanId: 4 },
          { id: 6, name: "Circles", status: "in-progress", hours: 12, lessonPlanId: 5 },
          { id: 7, name: "Coordinate Geometry", status: "pending", hours: 10, lessonPlanId: null },
        ]
      },
      {
        id: 3,
        name: "Trigonometry",
        topics: [
          { id: 8, name: "Introduction to Trigonometry", status: "pending", hours: 8, lessonPlanId: null },
          { id: 9, name: "Trigonometric Identities", status: "pending", hours: 10, lessonPlanId: null },
        ]
      }
    ]
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "in-progress":
        return <Clock className="h-5 w-5 text-orange-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-300" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="default">Completed</Badge>;
      case "in-progress":
        return <Badge variant="secondary">In Progress</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

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
              <BookOpen className="h-8 w-8 text-primary" />
              Syllabus Management
            </h1>
            <p className="text-muted-foreground mt-1">Track syllabus completion and topic progress</p>
          </div>
        </div>

        <Card className="border-2 border-primary">
          <CardHeader>
            <CardTitle className="text-2xl">{syllabusData.subject}</CardTitle>
            <CardDescription>Overall syllabus completion status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Topics Completed</span>
                  <span className="text-sm font-semibold">
                    {syllabusData.completedTopics} / {syllabusData.totalTopics} ({Math.round((syllabusData.completedTopics / syllabusData.totalTopics) * 100)}%)
                  </span>
                </div>
                <Progress value={(syllabusData.completedTopics / syllabusData.totalTopics) * 100} className="h-3" />
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Estimated Hours</span>
                  <span className="text-sm font-semibold">
                    {syllabusData.completedHours} / {syllabusData.estimatedHours} hours
                  </span>
                </div>
                <Progress value={(syllabusData.completedHours / syllabusData.estimatedHours) * 100} className="h-3" />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Topics</CardDescription>
              <CardTitle className="text-3xl">{syllabusData.totalTopics}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Completed</CardDescription>
              <CardTitle className="text-3xl text-green-600">{syllabusData.completedTopics}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>In Progress</CardDescription>
              <CardTitle className="text-3xl text-orange-600">{syllabusData.inProgressTopics}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Pending</CardDescription>
              <CardTitle className="text-3xl text-gray-600">
                {syllabusData.totalTopics - syllabusData.completedTopics - syllabusData.inProgressTopics}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsList>All Units</TabsList>
            <TabsTrigger value="completed">Completed</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <div className="space-y-4">
              {syllabusData.units.map((unit) => (
                <Card key={unit.id}>
                  <CardHeader>
                    <CardTitle className="text-xl">Unit {unit.id}: {unit.name}</CardTitle>
                    <CardDescription>
                      {unit.topics.filter(t => t.status === "completed").length} / {unit.topics.length} topics completed
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {unit.topics.map((topic) => (
                        <div key={topic.id} className="flex items-center justify-between p-4 border rounded-lg">
                          <div className="flex items-center gap-3 flex-1">
                            {getStatusIcon(topic.status)}
                            <div className="flex-1">
                              <p className="font-medium">{topic.name}</p>
                              <p className="text-sm text-muted-foreground">
                                Estimated: {topic.hours} hours
                                {topic.lessonPlanId && " • Lesson plan created"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusBadge(topic.status)}
                            {topic.lessonPlanId ? (
                              <Button variant="outline" size="sm">View Plan</Button>
                            ) : (
                              <Button size="sm">Create Plan</Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="completed">
            <Card>
              <CardHeader>
                <CardTitle>Completed Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pending">
            <Card>
              <CardHeader>
                <CardTitle>Pending Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default SyllabusPage;
