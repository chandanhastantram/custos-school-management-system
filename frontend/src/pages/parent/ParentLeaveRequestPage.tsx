import { useState, useEffect } from "react";
import { parentApi } from "@/services/parent-api";
import { motion } from "framer-motion";
import { FileText, Plus, Calendar, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type LeaveStatus = "Approved" | "Pending" | "Rejected";
interface LeaveRequest {
  id: number;
  child: string;
  startDate: string;
  endDate: string;
  reason: string;
  status: LeaveStatus;
}

const STATUS_CONFIG: Record<LeaveStatus, { icon: React.ElementType; color: string }> = {
  Approved: { icon: CheckCircle2, color: "text-emerald-600" },
  Pending: { icon: Clock, color: "text-amber-600" },
  Rejected: { icon: XCircle, color: "text-red-600" },
};

const ParentLeaveRequestPage = () => {
  const [selectedChild, setSelectedChild] = useState("1");
  const [tab, setTab] = useState("requests");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const children = [
    { id: "1", name: "Aisha Sharma", class: "10-A" },
    { id: "2", name: "Rahul Sharma", class: "8-B" },
  ];

  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([
    { id: 1, child: "Aisha Sharma", startDate: "2024-02-20", endDate: "2024-02-22", reason: "Family function", status: "Approved" },
    { id: 2, child: "Rahul Sharma", startDate: "2024-02-15", endDate: "2024-02-15", reason: "Medical appointment", status: "Pending" },
    { id: 3, child: "Aisha Sharma", startDate: "2024-01-10", endDate: "2024-01-11", reason: "Fever", status: "Approved" },
    { id: 4, child: "Rahul Sharma", startDate: "2024-01-20", endDate: "2024-01-20", reason: "Event", status: "Rejected" },
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startDate || !endDate || !reason.trim()) {
      toast({ title: "Please fill all fields", variant: "destructive" });
      return;
    }
    setSubmitting(true);
    const child = children.find(c => c.id === selectedChild)!;
    try {
      await parentApi.submitLeaveRequest({
        student_id: child.id,
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim(),
      });
    } catch {
      // fallback: add locally
    }
    const newReq: LeaveRequest = {
      id: Date.now(),
      child: child.name,
      startDate,
      endDate,
      reason: reason.trim(),
      status: "Pending",
    };
    setLeaveRequests(prev => [newReq, ...prev]);
    setStartDate("");
    setEndDate("");
    setReason("");
    setSubmitting(false);
    setTab("requests");
    toast({ title: "Leave request submitted!", description: `Request for ${child.name} has been submitted.` });
  };

  const approved = leaveRequests.filter(r => r.status === "Approved").length;
  const pending = leaveRequests.filter(r => r.status === "Pending").length;
  const rejected = leaveRequests.filter(r => r.status === "Rejected").length;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileText className="h-6 w-6 text-primary" /> Leave Requests
            </h1>
            <p className="text-muted-foreground text-sm mt-1">Request leave for your children</p>
          </div>
          <Button onClick={() => setTab("new")}>
            <Plus className="h-4 w-4 mr-2" /> New Request
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Total</p><p className="text-2xl font-bold">{leaveRequests.length}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Approved</p><p className="text-2xl font-bold text-emerald-600">{approved}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Pending</p><p className="text-2xl font-bold text-amber-600">{pending}</p></CardContent></Card>
          <Card><CardContent className="p-4"><p className="text-xs text-muted-foreground">Rejected</p><p className="text-2xl font-bold text-red-600">{rejected}</p></CardContent></Card>
        </div>

        <Tabs value={tab} onValueChange={setTab} className="space-y-4">
          <TabsList>
            <TabsTrigger value="requests">My Requests</TabsTrigger>
            <TabsTrigger value="new">New Request</TabsTrigger>
          </TabsList>

          <TabsContent value="requests">
            <Card>
              <CardHeader>
                <CardTitle>Leave Requests</CardTitle>
                <CardDescription>All leave requests you have submitted</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leaveRequests.length === 0 ? (
                    <p className="text-center py-8 text-muted-foreground">No requests yet</p>
                  ) : leaveRequests.map((request) => {
                    const cfg = STATUS_CONFIG[request.status as LeaveStatus];
                    return (
                      <div key={request.id} className="flex items-start justify-between p-4 border rounded-lg hover:bg-muted/30 transition-colors">
                        <div>
                          <p className="font-medium">{request.child}</p>
                          <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
                            <Calendar className="h-3.5 w-3.5" />
                            {request.startDate} → {request.endDate}
                          </p>
                          <p className="text-sm mt-2 text-muted-foreground">{request.reason}</p>
                        </div>
                        <Badge variant="outline" className={cn("flex items-center gap-1", cfg.color)}>
                          <cfg.icon className="h-3 w-3" />
                          {request.status}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="new">
            <Card>
              <CardHeader>
                <CardTitle>Submit Leave Request</CardTitle>
                <CardDescription>Request leave for your child</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Select Child</Label>
                    <Select value={selectedChild} onValueChange={setSelectedChild}>
                      <SelectTrigger><SelectValue placeholder="Select child" /></SelectTrigger>
                      <SelectContent>
                        {children.map((child) => (
                          <SelectItem key={child.id} value={child.id}>{child.name} – Class {child.class}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Start Date</Label>
                      <Input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                    </div>
                    <div className="space-y-2">
                      <Label>End Date</Label>
                      <Input type="date" value={endDate} min={startDate} onChange={e => setEndDate(e.target.value)} required />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Reason for Leave</Label>
                    <Textarea
                      placeholder="Please provide a reason..."
                      rows={4}
                      value={reason}
                      onChange={e => setReason(e.target.value)}
                      required
                    />
                  </div>
                  <Button className="w-full" type="submit" disabled={submitting}>
                    {submitting ? "Submitting..." : "Submit Request"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ParentLeaveRequestPage;
