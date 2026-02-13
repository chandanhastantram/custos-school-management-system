import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Calendar, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";

const ExamRegistrationPage = () => {
  const [selectedExams, setSelectedExams] = useState<number[]>([]);

  const upcomingExams = [
    { 
      id: 1, 
      name: "Mid-Term Examination - 2024", 
      startDate: "2024-03-15", 
      endDate: "2024-03-25",
      subjects: ["Mathematics", "Physics", "Chemistry", "English", "Biology"],
      registrationDeadline: "2024-03-10",
      eligible: true,
      registered: false,
      fee: "$50"
    },
    { 
      id: 2, 
      name: "Final Examination - 2024", 
      startDate: "2024-05-20", 
      endDate: "2024-06-05",
      subjects: ["All Subjects"],
      registrationDeadline: "2024-05-15",
      eligible: true,
      registered: false,
      fee: "$100"
    },
  ];

  const registeredExams = [
    {
      id: 3,
      name: "Unit Test - January 2024",
      startDate: "2024-01-20",
      registeredOn: "2024-01-10",
      status: "Completed"
    }
  ];

  const handleToggleExam = (examId: number) => {
    setSelectedExams(prev => 
      prev.includes(examId) 
        ? prev.filter(id => id !== examId)
        : [...prev, examId]
    );
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
              <FileText className="h-8 w-8 text-primary" />
              Exam Registration
            </h1>
            <p className="text-muted-foreground mt-1">Register for upcoming examinations</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Upcoming Exams</CardDescription>
              <CardTitle className="text-3xl">2</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Registered</CardDescription>
              <CardTitle className="text-3xl text-green-600">1</CardTitle>
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
              <CardDescription>Completed</CardDescription>
              <CardTitle className="text-3xl">1</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="upcoming" className="space-y-4">
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming Exams</TabsTrigger>
            <TabsTrigger value="registered">My Registrations</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming">
            <Card>
              <CardHeader>
                <CardTitle>Available Examinations</CardTitle>
                <CardDescription>Register before the deadline</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {upcomingExams.map((exam) => (
                    <Card key={exam.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <Checkbox 
                              checked={selectedExams.includes(exam.id)}
                              onCheckedChange={() => handleToggleExam(exam.id)}
                              disabled={!exam.eligible || exam.registered}
                            />
                            <div className="flex-1">
                              <CardTitle className="text-lg">{exam.name}</CardTitle>
                              <CardDescription className="flex flex-col gap-1 mt-2">
                                <span className="flex items-center gap-1">
                                  <Calendar className="h-4 w-4" />
                                  {exam.startDate} to {exam.endDate}
                                </span>
                                <span className="text-sm">
                                  Registration Deadline: {exam.registrationDeadline}
                                </span>
                              </CardDescription>
                            </div>
                          </div>
                          <div className="flex flex-col gap-2 items-end">
                            {exam.eligible ? (
                              <Badge variant="default">Eligible</Badge>
                            ) : (
                              <Badge variant="destructive">Not Eligible</Badge>
                            )}
                            {exam.registered && (
                              <Badge variant="secondary">Registered</Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm font-medium mb-1">Subjects:</p>
                            <div className="flex flex-wrap gap-2">
                              {exam.subjects.map((subject, idx) => (
                                <Badge key={idx} variant="outline">{subject}</Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between pt-2">
                            <span className="text-lg font-semibold">Fee: {exam.fee}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {selectedExams.length > 0 && (
                    <Alert>
                      <CheckCircle2 className="h-4 w-4" />
                      <AlertTitle>Ready to Register</AlertTitle>
                      <AlertDescription>
                        You have selected {selectedExams.length} exam(s). Click below to proceed with registration.
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button 
                    className="w-full" 
                    size="lg"
                    disabled={selectedExams.length === 0}
                  >
                    Register for Selected Exams ({selectedExams.length})
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="registered">
            <Card>
              <CardHeader>
                <CardTitle>My Exam Registrations</CardTitle>
                <CardDescription>Previously registered examinations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {registeredExams.map((exam) => (
                    <div key={exam.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-semibold">{exam.name}</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          Registered on: {exam.registeredOn}
                        </p>
                      </div>
                      <Badge variant="secondary">{exam.status}</Badge>
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

export default ExamRegistrationPage;
