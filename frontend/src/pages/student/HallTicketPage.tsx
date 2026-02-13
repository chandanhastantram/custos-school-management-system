import { motion } from "framer-motion";
import { Download, Printer, QrCode, Calendar, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const HallTicketPage = () => {
  const hallTicket = {
    examName: "Mid-Term Examination - 2024",
    examType: "Theory",
    rollNumber: "10A-001",
    studentName: "John Doe",
    class: "10-A",
    section: "A",
    photo: null,
    examCenter: "Main Building, Room 101",
    centerAddress: "CUSTOS School, 123 Education Street, City",
    examDates: [
      { date: "2024-03-15", day: "Monday", subject: "Mathematics", time: "09:00 AM - 12:00 PM" },
      { date: "2024-03-16", day: "Tuesday", subject: "Physics", time: "09:00 AM - 12:00 PM" },
      { date: "2024-03-17", day: "Wednesday", subject: "Chemistry", time: "09:00 AM - 12:00 PM" },
      { date: "2024-03-18", day: "Thursday", subject: "English", time: "09:00 AM - 12:00 PM" },
      { date: "2024-03-19", day: "Friday", subject: "Biology", time: "09:00 AM - 12:00 PM" },
    ],
    instructions: [
      "Bring this hall ticket to the examination center",
      "Arrive at least 30 minutes before the exam",
      "Carry a valid ID proof",
      "Mobile phones are strictly prohibited",
      "Follow the exam center rules and regulations"
    ],
    issueDate: "2024-03-01",
    qrCode: "EXAM-2024-10A001"
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
              <QrCode className="h-8 w-8 text-primary" />
              Hall Ticket
            </h1>
            <p className="text-muted-foreground mt-1">Download your examination hall ticket</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button>
              <Download className="h-4 w-4 mr-2" />
              Download PDF
            </Button>
          </div>
        </div>

        {/* Hall Ticket Preview */}
        <Card className="border-2">
          <CardHeader className="bg-primary/5">
            <div className="text-center">
              <CardTitle className="text-2xl">CUSTOS SCHOOL</CardTitle>
              <CardDescription className="text-base mt-2">
                Examination Hall Ticket
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {/* Student Info Section */}
            <div className="flex items-start gap-6 mb-6">
              <Avatar className="h-32 w-32 border-2">
                <AvatarImage src={hallTicket.photo || undefined} />
                <AvatarFallback className="text-3xl">
                  {hallTicket.studentName.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Student Name</p>
                    <p className="font-semibold text-lg">{hallTicket.studentName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Roll Number</p>
                    <p className="font-semibold text-lg">{hallTicket.rollNumber}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Class</p>
                    <p className="font-semibold">{hallTicket.class}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Examination</p>
                    <p className="font-semibold">{hallTicket.examName}</p>
                  </div>
                </div>
              </div>
              <div className="text-center">
                <div className="h-24 w-24 bg-muted rounded flex items-center justify-center mb-2">
                  <QrCode className="h-16 w-16" />
                </div>
                <p className="text-xs text-muted-foreground">Verification Code</p>
              </div>
            </div>

            <Separator className="my-6" />

            {/* Exam Center */}
            <div className="mb-6">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Examination Center
              </h3>
              <div className="bg-muted/50 p-4 rounded-lg">
                <p className="font-medium">{hallTicket.examCenter}</p>
                <p className="text-sm text-muted-foreground mt-1">{hallTicket.centerAddress}</p>
              </div>
            </div>

            <Separator className="my-6" />

            {/* Exam Schedule */}
            <div className="mb-6">
              <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Examination Schedule
              </h3>
              <div className="space-y-2">
                {hallTicket.examDates.map((exam, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="text-center min-w-[80px]">
                        <p className="font-semibold">{exam.date}</p>
                        <p className="text-sm text-muted-foreground">{exam.day}</p>
                      </div>
                      <Separator orientation="vertical" className="h-10" />
                      <div>
                        <p className="font-medium">{exam.subject}</p>
                        <p className="text-sm text-muted-foreground">{exam.time}</p>
                      </div>
                    </div>
                    <Badge variant="outline">Theory</Badge>
                  </div>
                ))}
              </div>
            </div>

            <Separator className="my-6" />

            {/* Instructions */}
            <div>
              <h3 className="font-semibold text-lg mb-3">Important Instructions</h3>
              <ul className="space-y-2">
                {hallTicket.instructions.map((instruction, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-primary mt-1">•</span>
                    <span>{instruction}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Separator className="my-6" />

            {/* Footer */}
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <p>Issue Date: {hallTicket.issueDate}</p>
              <p>Verification Code: {hallTicket.qrCode}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Download Options</CardTitle>
            <CardDescription>Save or print your hall ticket</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button className="flex-1" size="lg">
                <Download className="h-5 w-5 mr-2" />
                Download as PDF
              </Button>
              <Button variant="outline" className="flex-1" size="lg">
                <Printer className="h-5 w-5 mr-2" />
                Print Hall Ticket
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default HallTicketPage;
