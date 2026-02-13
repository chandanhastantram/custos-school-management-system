import { useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Plus, Search, BarChart3, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const FeedbackPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const surveys = [
    { id: 1, title: "Teacher Performance Evaluation", type: "Teacher", responses: 145, target: 200, status: "Active", endDate: "2024-02-28" },
    { id: 2, title: "Parent Satisfaction Survey", type: "Parent", responses: 89, target: 150, status: "Active", endDate: "2024-03-15" },
    { id: 3, title: "Student Wellbeing Check", type: "Student", responses: 320, target: 300, status: "Completed", endDate: "2024-02-10" },
  ];

  const recentFeedback = [
    { id: 1, from: "John Doe (Parent)", subject: "Excellent teaching quality", rating: 5, date: "2024-02-13", category: "Academic" },
    { id: 2, from: "Jane Smith (Student)", subject: "Need more library books", rating: 3, date: "2024-02-12", category: "Facilities" },
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
              <MessageSquare className="h-8 w-8 text-primary" />
              Feedback & Surveys
            </h1>
            <p className="text-muted-foreground mt-1">Collect and analyze stakeholder feedback</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <BarChart3 className="h-4 w-4 mr-2" />
              View Analytics
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Survey
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Surveys</CardDescription>
              <CardTitle className="text-3xl">5</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Responses</CardDescription>
              <CardTitle className="text-3xl">1,234</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg. Satisfaction</CardDescription>
              <CardTitle className="text-3xl">4.2/5</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Month</CardDescription>
              <CardTitle className="text-3xl flex items-center gap-1">
                <TrendingUp className="h-5 w-5 text-green-500" />
                +12%
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="surveys" className="space-y-4">
          <TabsList>
            <TabsTrigger value="surveys">Surveys</TabsTrigger>
            <TabsTrigger value="feedback">Recent Feedback</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="surveys">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Active Surveys</CardTitle>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search surveys..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {surveys.map((survey) => (
                    <Card key={survey.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg">{survey.title}</CardTitle>
                            <CardDescription>
                              Target: {survey.type} • Ends: {survey.endDate}
                            </CardDescription>
                          </div>
                          <Badge variant={survey.status === "Active" ? "default" : "secondary"}>
                            {survey.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Response Rate</span>
                            <span className="font-medium">
                              {survey.responses} / {survey.target} ({Math.round((survey.responses / survey.target) * 100)}%)
                            </span>
                          </div>
                          <Progress value={(survey.responses / survey.target) * 100} className="h-2" />
                          <div className="flex gap-2 mt-4">
                            <Button variant="outline" size="sm" className="flex-1">View Results</Button>
                            <Button size="sm" className="flex-1">Send Reminder</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="feedback">
            <Card>
              <CardHeader>
                <CardTitle>Recent Feedback</CardTitle>
                <CardDescription>Latest feedback from stakeholders</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>From</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Rating</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentFeedback.map((feedback) => (
                      <TableRow key={feedback.id}>
                        <TableCell className="font-medium">{feedback.from}</TableCell>
                        <TableCell>{feedback.subject}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{feedback.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {"⭐".repeat(feedback.rating)}
                          </div>
                        </TableCell>
                        <TableCell>{feedback.date}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">View</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics">
            <Card>
              <CardHeader>
                <CardTitle>Feedback Analytics</CardTitle>
                <CardDescription>Trends and insights from feedback data</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Analytics dashboard coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default FeedbackPage;
