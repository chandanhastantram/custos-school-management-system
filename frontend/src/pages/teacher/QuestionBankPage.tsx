import { useState } from "react";
import { motion } from "framer-motion";
import { HelpCircle, Plus, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const QuestionBankPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const questions = [
    { id: 1, question: "What is the quadratic formula?", type: "MCQ", subject: "Mathematics", difficulty: "Medium", blooms: "Remember", usage: 12 },
    { id: 2, question: "Explain photosynthesis process", type: "Short Answer", subject: "Biology", difficulty: "Hard", blooms: "Understand", usage: 8 },
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
              <HelpCircle className="h-8 w-8 text-primary" />
              Question Bank
            </h1>
            <p className="text-muted-foreground mt-1">Create and manage assessment questions</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Sparkles className="h-4 w-4 mr-2" />
              AI Generate
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Question
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Questions</CardDescription>
              <CardTitle className="text-3xl">245</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>MCQ</CardDescription>
              <CardTitle className="text-3xl">180</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Short Answer</CardDescription>
              <CardTitle className="text-3xl">45</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Essay</CardDescription>
              <CardTitle className="text-3xl">20</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">All Questions</TabsTrigger>
            <TabsTrigger value="mcq">MCQ</TabsTrigger>
            <TabsTrigger value="short">Short Answer</TabsTrigger>
            <TabsTrigger value="essay">Essay</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Question Library</CardTitle>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search questions..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Question</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Subject</TableHead>
                      <TableHead>Difficulty</TableHead>
                      <TableHead>Bloom's Level</TableHead>
                      <TableHead>Usage</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {questions.map((q) => (
                      <TableRow key={q.id}>
                        <TableCell className="font-medium max-w-xs truncate">{q.question}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{q.type}</Badge>
                        </TableCell>
                        <TableCell>{q.subject}</TableCell>
                        <TableCell>
                          <Badge variant={q.difficulty === "Hard" ? "destructive" : q.difficulty === "Medium" ? "default" : "secondary"}>
                            {q.difficulty}
                          </Badge>
                        </TableCell>
                        <TableCell>{q.blooms}</TableCell>
                        <TableCell>{q.usage}x</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">Edit</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mcq">
            <Card>
              <CardHeader>
                <CardTitle>Multiple Choice Questions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="short">
            <Card>
              <CardHeader>
                <CardTitle>Short Answer Questions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="essay">
            <Card>
              <CardHeader>
                <CardTitle>Essay Questions</CardTitle>
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

export default QuestionBankPage;
