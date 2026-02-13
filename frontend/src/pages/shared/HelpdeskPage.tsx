import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  HelpCircle, Search, Plus, MessageSquare, Clock, CheckCircle2,
  AlertCircle, ChevronRight, ChevronDown, MoreHorizontal, Send,
  FileText, Tag, User, Filter, ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "@/components/ui/tabs";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// Types
type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
type TicketPriority = "low" | "medium" | "high" | "urgent";

interface Ticket {
  id: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: string;
  createdAt: string;
  updatedAt: string;
  responses: number;
}

interface FAQ {
  question: string;
  answer: string;
  category: string;
}

// Demo data
const DEMO_TICKETS: Ticket[] = [
  { id: "TKT-001", subject: "Unable to access attendance module", description: "Getting error when trying to mark attendance", status: "open", priority: "high", category: "Technical", createdAt: "2024-11-15", updatedAt: "2024-11-15", responses: 0 },
  { id: "TKT-002", subject: "Fee payment not reflecting", description: "Paid fees but status still shows pending", status: "in_progress", priority: "urgent", category: "Finance", createdAt: "2024-11-14", updatedAt: "2024-11-15", responses: 2 },
  { id: "TKT-003", subject: "Request for leave application", description: "Need to apply for medical leave", status: "resolved", priority: "medium", category: "Academic", createdAt: "2024-11-10", updatedAt: "2024-11-12", responses: 3 },
  { id: "TKT-004", subject: "Report card download issue", description: "PDF download not working", status: "closed", priority: "low", category: "Technical", createdAt: "2024-11-08", updatedAt: "2024-11-09", responses: 1 },
];

const DEMO_FAQS: FAQ[] = [
  { question: "How do I reset my password?", answer: "Go to the login page and click 'Forgot Password'. Enter your registered email address and you'll receive a password reset link within 5 minutes.", category: "Account" },
  { question: "How can I pay fees online?", answer: "Navigate to Finance > Pay Fees from the dashboard. You can pay using Credit/Debit Card, UPI, or Net Banking. All transactions are secured with 256-bit encryption.", category: "Finance" },
  { question: "How do I view my child's attendance?", answer: "Go to the Parent Portal and click on 'Attendance' from the dashboard. You can view daily, weekly, and monthly attendance reports.", category: "Attendance" },
  { question: "How to download report cards?", answer: "Navigate to Results > Report Cards. Select the examination and click the download button. Report cards are available as PDF files.", category: "Academic" },
  { question: "How do I contact a teacher?", answer: "Use the Messages section to send direct messages to teachers. You can also request a meeting through the 'Schedule Meeting' button.", category: "Communication" },
  { question: "What are the school timings?", answer: "School operates from 8:00 AM to 3:00 PM, Monday to Saturday. The assembly starts at 7:45 AM.", category: "General" },
];

const STATUS_CONFIG: Record<TicketStatus, { label: string; color: string; icon: React.ElementType }> = {
  open: { label: "Open", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300", icon: AlertCircle },
  in_progress: { label: "In Progress", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300", icon: Clock },
  resolved: { label: "Resolved", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300", icon: CheckCircle2 },
  closed: { label: "Closed", color: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300", icon: CheckCircle2 },
};

const PRIORITY_CONFIG: Record<TicketPriority, { label: string; color: string }> = {
  low: { label: "Low", color: "bg-gray-100 text-gray-600" },
  medium: { label: "Medium", color: "bg-blue-100 text-blue-600" },
  high: { label: "High", color: "bg-orange-100 text-orange-600" },
  urgent: { label: "Urgent", color: "bg-red-100 text-red-600" },
};

const HelpdeskPage = () => {
  const [tab, setTab] = useState("tickets");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [showNewTicket, setShowNewTicket] = useState(false);

  const stats = useMemo(() => ({
    open: DEMO_TICKETS.filter(t => t.status === "open").length,
    inProgress: DEMO_TICKETS.filter(t => t.status === "in_progress").length,
    resolved: DEMO_TICKETS.filter(t => t.status === "resolved" || t.status === "closed").length,
    total: DEMO_TICKETS.length,
  }), []);

  const filteredTickets = useMemo(() => {
    return DEMO_TICKETS.filter(ticket => {
      const matchesSearch = ticket.subject.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "all" || ticket.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [search, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Help Desk</h1>
          <p className="text-muted-foreground text-sm">Get support and find answers</p>
        </div>
        <Button onClick={() => setShowNewTicket(true)}>
          <Plus className="h-4 w-4 mr-1" /> New Ticket
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Open Tickets", value: stats.open, icon: AlertCircle, color: "text-blue-600" },
          { label: "In Progress", value: stats.inProgress, icon: Clock, color: "text-amber-600" },
          { label: "Resolved", value: stats.resolved, icon: CheckCircle2, color: "text-emerald-600" },
          { label: "Total Tickets", value: stats.total, icon: FileText, color: "text-purple-600" },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", stat.color.replace("text-", "bg-").replace("-600", "-100"), "dark:bg-opacity-20")}>
                <stat.icon className={cn("h-5 w-5", stat.color)} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className={cn("text-lg font-bold", stat.color)}>{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="tickets">My Tickets</TabsTrigger>
            <TabsTrigger value="faq">FAQ</TabsTrigger>
          </TabsList>
          {tab === "tickets" && (
            <div className="flex items-center gap-2">
              <div className="relative max-w-xs">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search tickets..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>{config.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Tickets Tab */}
        <TabsContent value="tickets" className="space-y-4">
          {filteredTickets.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <HelpCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No tickets found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredTickets.map((ticket, i) => {
                const StatusIcon = STATUS_CONFIG[ticket.status].icon;
                return (
                  <motion.div
                    key={ticket.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card className="hover:shadow-md transition-shadow cursor-pointer">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", STATUS_CONFIG[ticket.status].color)}>
                            <StatusIcon className="h-5 w-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="font-medium text-sm">{ticket.subject}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">{ticket.id} · {ticket.category}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge className={cn("text-xs", PRIORITY_CONFIG[ticket.priority].color)}>
                                  {PRIORITY_CONFIG[ticket.priority].label}
                                </Badge>
                                <Badge className={cn("text-xs", STATUS_CONFIG[ticket.status].color)}>
                                  {STATUS_CONFIG[ticket.status].label}
                                </Badge>
                              </div>
                            </div>
                            <p className="text-sm text-muted-foreground mt-2 line-clamp-1">{ticket.description}</p>
                            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                              <span>Created: {format(new Date(ticket.createdAt), "MMM d, yyyy")}</span>
                              <span className="flex items-center gap-1">
                                <MessageSquare className="h-3 w-3" /> {ticket.responses} replies
                              </span>
                            </div>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* FAQ Tab */}
        <TabsContent value="faq" className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Frequently Asked Questions</CardTitle>
              <CardDescription>Find quick answers to common questions</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {DEMO_FAQS.map((faq, i) => (
                  <AccordionItem key={i} value={`faq-${i}`}>
                    <AccordionTrigger className="text-left text-sm">
                      <div className="flex items-center gap-2">
                        <HelpCircle className="h-4 w-4 text-primary shrink-0" />
                        {faq.question}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="text-sm text-muted-foreground pl-6">
                      {faq.answer}
                      <Badge variant="outline" className="mt-2 ml-0">{faq.category}</Badge>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default HelpdeskPage;
