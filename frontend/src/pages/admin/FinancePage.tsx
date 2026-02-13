import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  DollarSign, Users, Receipt, AlertCircle, TrendingUp, TrendingDown,
  Loader2, Download, Filter, Search, Plus, MoreHorizontal, Eye,
  CheckCircle2, XCircle, Clock, CreditCard, Banknote, Building2,
  ChevronDown, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
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
import { Progress } from "@/components/ui/progress";
import apiClient from "@/lib/api-client";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

// Types
type InvoiceStatus = "pending" | "partial" | "paid" | "overdue" | "cancelled";
type PaymentMethod = "cash" | "upi" | "card" | "bank_transfer" | "cheque" | "online";

interface Invoice {
  id: string;
  invoiceNumber: string;
  studentId: string;
  studentName: string;
  className: string;
  invoiceDate: string;
  dueDate: string;
  totalAmount: number;
  amountPaid: number;
  balanceDue: number;
  status: InvoiceStatus;
  installmentNo: number;
}

interface Payment {
  id: string;
  receiptNumber: string;
  studentName: string;
  invoiceNumber: string;
  amountPaid: number;
  paymentDate: string;
  method: PaymentMethod;
  recordedBy: string;
}

interface ClassFeeSummary {
  classId: string;
  className: string;
  totalStudents: number;
  totalDue: number;
  totalCollected: number;
  collectionPercentage: number;
  overdueCount: number;
}

// Demo data
const DEMO_INVOICES: Invoice[] = [
  { id: "1", invoiceNumber: "INV-2024-0001", studentId: "st1", studentName: "Aisha Sharma", className: "Class 10-A", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 45000, amountPaid: 45000, balanceDue: 0, status: "paid", installmentNo: 1 },
  { id: "2", invoiceNumber: "INV-2024-0002", studentId: "st2", studentName: "Rahul Verma", className: "Class 10-A", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 45000, amountPaid: 22500, balanceDue: 22500, status: "partial", installmentNo: 1 },
  { id: "3", invoiceNumber: "INV-2024-0003", studentId: "st3", studentName: "Priya Patel", className: "Class 9-A", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 42000, amountPaid: 0, balanceDue: 42000, status: "overdue", installmentNo: 1 },
  { id: "4", invoiceNumber: "INV-2024-0004", studentId: "st4", studentName: "Vikram Singh", className: "Class 10-B", invoiceDate: "2024-01-10", dueDate: "2024-02-15", totalAmount: 45000, amountPaid: 0, balanceDue: 45000, status: "pending", installmentNo: 1 },
  { id: "5", invoiceNumber: "INV-2024-0005", studentId: "st5", studentName: "Nisha Gupta", className: "Class 9-A", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 42000, amountPaid: 42000, balanceDue: 0, status: "paid", installmentNo: 1 },
  { id: "6", invoiceNumber: "INV-2024-0006", studentId: "st6", studentName: "Arjun Kumar", className: "Class 10-A", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 45000, amountPaid: 45000, balanceDue: 0, status: "paid", installmentNo: 1 },
  { id: "7", invoiceNumber: "INV-2024-0007", studentId: "st7", studentName: "Sneha Reddy", className: "Class 9-B", invoiceDate: "2024-01-10", dueDate: "2024-02-15", totalAmount: 42000, amountPaid: 21000, balanceDue: 21000, status: "partial", installmentNo: 1 },
  { id: "8", invoiceNumber: "INV-2024-0008", studentId: "st8", studentName: "Karan Mehta", className: "Class 10-B", invoiceDate: "2024-01-10", dueDate: "2024-01-31", totalAmount: 45000, amountPaid: 0, balanceDue: 45000, status: "overdue", installmentNo: 1 },
];

const DEMO_PAYMENTS: Payment[] = [
  { id: "p1", receiptNumber: "RCP-2024-0001", studentName: "Aisha Sharma", invoiceNumber: "INV-2024-0001", amountPaid: 45000, paymentDate: "2024-01-15", method: "upi", recordedBy: "Admin" },
  { id: "p2", receiptNumber: "RCP-2024-0002", studentName: "Rahul Verma", invoiceNumber: "INV-2024-0002", amountPaid: 22500, paymentDate: "2024-01-20", method: "cash", recordedBy: "Admin" },
  { id: "p3", receiptNumber: "RCP-2024-0003", studentName: "Nisha Gupta", invoiceNumber: "INV-2024-0005", amountPaid: 42000, paymentDate: "2024-01-18", method: "bank_transfer", recordedBy: "Admin" },
  { id: "p4", receiptNumber: "RCP-2024-0004", studentName: "Arjun Kumar", invoiceNumber: "INV-2024-0006", amountPaid: 45000, paymentDate: "2024-01-25", method: "card", recordedBy: "Admin" },
  { id: "p5", receiptNumber: "RCP-2024-0005", studentName: "Sneha Reddy", invoiceNumber: "INV-2024-0007", amountPaid: 21000, paymentDate: "2024-01-28", method: "cheque", recordedBy: "Admin" },
];

const DEMO_CLASS_FEE_SUMMARY: ClassFeeSummary[] = [
  { classId: "c1", className: "Class 10-A", totalStudents: 30, totalDue: 1350000, totalCollected: 1215000, collectionPercentage: 90, overdueCount: 2 },
  { classId: "c2", className: "Class 10-B", totalStudents: 28, totalDue: 1260000, totalCollected: 882000, collectionPercentage: 70, overdueCount: 5 },
  { classId: "c3", className: "Class 9-A", totalStudents: 32, totalDue: 1344000, totalCollected: 1075200, collectionPercentage: 80, overdueCount: 3 },
  { classId: "c4", className: "Class 9-B", totalStudents: 30, totalDue: 1260000, totalCollected: 1008000, collectionPercentage: 80, overdueCount: 4 },
];

const STATUS_CONFIG: Record<InvoiceStatus, { label: string; color: string; bgColor: string }> = {
  paid: { label: "Paid", color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-900/30" },
  partial: { label: "Partial", color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" },
  pending: { label: "Pending", color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-900/30" },
  overdue: { label: "Overdue", color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-900/30" },
  cancelled: { label: "Cancelled", color: "text-gray-600", bgColor: "bg-gray-100 dark:bg-gray-900/30" },
};

const METHOD_CONFIG: Record<PaymentMethod, { label: string; icon: React.ElementType }> = {
  cash: { label: "Cash", icon: Banknote },
  upi: { label: "UPI", icon: Wallet },
  card: { label: "Card", icon: CreditCard },
  bank_transfer: { label: "Bank Transfer", icon: Building2 },
  cheque: { label: "Cheque", icon: Receipt },
  online: { label: "Online", icon: DollarSign },
};

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
  }).format(amount);
};

const FinancePage = () => {
  const [tab, setTab] = useState("overview");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [classFilter, setClassFilter] = useState<string>("all");
  const [demoMode] = useState(true);

  // Calculate overview stats
  const stats = useMemo(() => {
    const totalDue = DEMO_CLASS_FEE_SUMMARY.reduce((sum, c) => sum + c.totalDue, 0);
    const totalCollected = DEMO_CLASS_FEE_SUMMARY.reduce((sum, c) => sum + c.totalCollected, 0);
    const totalPending = totalDue - totalCollected;
    const overdueAmount = DEMO_INVOICES.filter(i => i.status === "overdue").reduce((sum, i) => sum + i.balanceDue, 0);
    
    return {
      totalDue,
      totalCollected,
      totalPending,
      overdueAmount,
      collectionRate: totalDue > 0 ? (totalCollected / totalDue) * 100 : 0,
      overdueCount: DEMO_INVOICES.filter(i => i.status === "overdue").length,
    };
  }, []);

  // Filter invoices
  const filteredInvoices = useMemo(() => {
    return DEMO_INVOICES.filter((invoice) => {
      const matchesSearch =
        invoice.studentName.toLowerCase().includes(search.toLowerCase()) ||
        invoice.invoiceNumber.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "all" || invoice.status === statusFilter;
      const matchesClass = classFilter === "all" || invoice.className === classFilter;
      return matchesSearch && matchesStatus && matchesClass;
    });
  }, [search, statusFilter, classFilter]);

  // Filter payments
  const filteredPayments = useMemo(() => {
    return DEMO_PAYMENTS.filter((payment) =>
      payment.studentName.toLowerCase().includes(search.toLowerCase()) ||
      payment.receiptNumber.toLowerCase().includes(search.toLowerCase())
    );
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Finance</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Manage fees, invoices, and payments</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" /> Generate Invoices
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="relative overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Total Due</p>
                <p className="text-xl font-bold">{formatCurrency(stats.totalDue)}</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                <Receipt className="h-5 w-5 text-muted-foreground" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="relative overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Collected</p>
                <p className="text-xl font-bold text-emerald-600">{formatCurrency(stats.totalCollected)}</p>
                <div className="flex items-center gap-1 text-xs text-emerald-600">
                  <ArrowUpRight className="h-3 w-3" />
                  {stats.collectionRate.toFixed(1)}%
                </div>
              </div>
              <div className="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="relative overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Pending</p>
                <p className="text-xl font-bold text-amber-600">{formatCurrency(stats.totalPending)}</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="relative overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Overdue</p>
                <p className="text-xl font-bold text-red-600">{formatCurrency(stats.overdueAmount)}</p>
                <p className="text-xs text-muted-foreground">{stats.overdueCount} invoices</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Collection by Class</CardTitle>
              <CardDescription>Fee collection status across all classes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {DEMO_CLASS_FEE_SUMMARY.map((c) => (
                  <div key={c.classId} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{c.className}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">{formatCurrency(c.totalCollected)} / {formatCurrency(c.totalDue)}</span>
                        <Badge variant={c.collectionPercentage >= 80 ? "default" : c.collectionPercentage >= 60 ? "secondary" : "destructive"}>
                          {c.collectionPercentage}%
                        </Badge>
                      </div>
                    </div>
                    <Progress value={c.collectionPercentage} className="h-2" />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{c.totalStudents} students</span>
                      {c.overdueCount > 0 && (
                        <span className="text-red-500">{c.overdueCount} overdue</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoices Tab */}
        <TabsContent value="invoices" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search student or invoice..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={classFilter} onValueChange={setClassFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Class" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Classes</SelectItem>
                {DEMO_CLASS_FEE_SUMMARY.map((c) => (
                  <SelectItem key={c.classId} value={c.className}>{c.className}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Invoices Table */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Invoice</TableHead>
                  <TableHead>Student</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Paid</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInvoices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                      No invoices found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredInvoices.map((invoice, i) => (
                    <motion.tr
                      key={invoice.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="border-b border-border hover:bg-muted/30 transition-colors"
                    >
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{invoice.invoiceNumber}</p>
                          <p className="text-xs text-muted-foreground">Due: {format(new Date(invoice.dueDate), "MMM d, yyyy")}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-7 w-7">
                            <AvatarFallback className="bg-primary/10 text-primary text-xs">
                              {invoice.studentName.split(" ").map(n => n[0]).join("")}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm">{invoice.studentName}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{invoice.className}</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(invoice.totalAmount)}</TableCell>
                      <TableCell className="text-right text-emerald-600">{formatCurrency(invoice.amountPaid)}</TableCell>
                      <TableCell className="text-right text-red-600">{formatCurrency(invoice.balanceDue)}</TableCell>
                      <TableCell>
                        <Badge className={cn("gap-1", STATUS_CONFIG[invoice.status].bgColor, STATUS_CONFIG[invoice.status].color)}>
                          {STATUS_CONFIG[invoice.status].label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Eye className="h-3.5 w-3.5 mr-2" /> View Details
                            </DropdownMenuItem>
                            {invoice.status !== "paid" && (
                              <DropdownMenuItem>
                                <CreditCard className="h-3.5 w-3.5 mr-2" /> Record Payment
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem>
                              <Download className="h-3.5 w-3.5 mr-2" /> Download PDF
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </motion.tr>
                  ))
                )}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>

        {/* Payments Tab */}
        <TabsContent value="payments" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search student or receipt..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          {/* Payments Table */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-border bg-card overflow-hidden"
          >
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Receipt</TableHead>
                  <TableHead>Student</TableHead>
                  <TableHead>Invoice</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPayments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No payments found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredPayments.map((payment, i) => {
                    const methodConfig = METHOD_CONFIG[payment.method];
                    return (
                      <motion.tr
                        key={payment.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="border-b border-border hover:bg-muted/30 transition-colors"
                      >
                        <TableCell className="font-medium text-sm">{payment.receiptNumber}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Avatar className="h-7 w-7">
                              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                {payment.studentName.split(" ").map(n => n[0]).join("")}
                              </AvatarFallback>
                            </Avatar>
                            <span className="text-sm">{payment.studentName}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{payment.invoiceNumber}</TableCell>
                        <TableCell className="text-right font-medium text-emerald-600">{formatCurrency(payment.amountPaid)}</TableCell>
                        <TableCell className="text-sm">{format(new Date(payment.paymentDate), "MMM d, yyyy")}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <methodConfig.icon className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="text-sm">{methodConfig.label}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <Eye className="h-3.5 w-3.5 mr-2" /> View Receipt
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Download className="h-3.5 w-3.5 mr-2" /> Download PDF
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </motion.tr>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FinancePage;
