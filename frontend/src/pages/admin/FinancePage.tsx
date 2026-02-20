import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  DollarSign, FileText, CreditCard, Users, TrendingUp,
  Search, Filter, Download, MoreHorizontal, Send,
  CheckCircle2, Clock, AlertCircle, RefreshCw, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { financeApi } from "@/services/finance-api";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface Invoice {
  id: string;
  student_name: string;
  class_name: string;
  amount: number;
  due_date: string;
  status: "paid" | "pending" | "overdue";
  description: string;
}

interface Payment {
  id: string;
  student_name: string;
  amount: number;
  payment_date: string;
  method: string;
  reference_no: string;
}

// Demo data
const DEMO_INVOICES: Invoice[] = [
  { id: "inv1", student_name: "Aisha Sharma", class_name: "10-A", amount: 45000, due_date: "2024-03-15", status: "paid", description: "Term 2 Fees" },
  { id: "inv2", student_name: "Rahul Verma", class_name: "10-A", amount: 45000, due_date: "2024-03-15", status: "pending", description: "Term 2 Fees" },
  { id: "inv3", student_name: "Priya Patel", class_name: "9-A", amount: 42000, due_date: "2024-02-28", status: "overdue", description: "Term 2 Fees" },
  { id: "inv4", student_name: "Vikram Singh", class_name: "10-B", amount: 45000, due_date: "2024-03-15", status: "paid", description: "Term 2 Fees" },
  { id: "inv5", student_name: "Nisha Gupta", class_name: "9-A", amount: 42000, due_date: "2024-03-15", status: "pending", description: "Term 2 Fees" },
];

const DEMO_PAYMENTS: Payment[] = [
  { id: "p1", student_name: "Aisha Sharma", amount: 45000, payment_date: "2024-03-10", method: "UPI", reference_no: "UPI-2024031001" },
  { id: "p2", student_name: "Vikram Singh", amount: 45000, payment_date: "2024-03-08", method: "Bank Transfer", reference_no: "NEFT-2024030801" },
  { id: "p3", student_name: "Arjun Kumar", amount: 42000, payment_date: "2024-03-05", method: "Cash", reference_no: "CASH-2024030501" },
];

const DEMO_CLASS_SUMMARY = [
  { class_name: "Class 10", collected: 1215000, total: 1350000, student_count: 30 },
  { class_name: "Class 9", collected: 1075200, total: 1344000, student_count: 32 },
  { class_name: "Class 8", collected: 882000, total: 1008000, student_count: 24 },
  { class_name: "Class 7", collected: 510000, total: 612000, student_count: 18 },
];

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, notation: "compact" }).format(amount);

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  paid: { label: "Paid", color: "text-emerald-600", bg: "bg-emerald-100 dark:bg-emerald-900/30" },
  pending: { label: "Pending", color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-900/30" },
  overdue: { label: "Overdue", color: "text-red-600", bg: "bg-red-100 dark:bg-red-900/30" },
};

const FinancePage = () => {
  const [tab, setTab] = useState("overview");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [demoMode, setDemoMode] = useState(false);

  const { data: invoiceData, isError: invoiceError, refetch: refetchInvoices } = useQuery({
    queryKey: ["finance-invoices", statusFilter],
    queryFn: () => financeApi.getInvoices({ status: statusFilter === "all" ? undefined : statusFilter }),
    retry: 1,
    staleTime: 30000,
  });

  const { data: paymentData } = useQuery({
    queryKey: ["finance-payments"],
    queryFn: () => financeApi.getPayments(),
    retry: 1,
    enabled: !demoMode,
  });

  const { data: summaryData } = useQuery({
    queryKey: ["finance-summary"],
    queryFn: () => financeApi.getFeeSummary(),
    retry: 1,
    enabled: !demoMode,
  });

  useEffect(() => {
    if (invoiceError && !demoMode) setDemoMode(true);
  }, [invoiceError, demoMode]);

  const invoices = demoMode ? DEMO_INVOICES : (invoiceData?.items || DEMO_INVOICES);
  const payments = demoMode ? DEMO_PAYMENTS : (paymentData?.items || DEMO_PAYMENTS);
  const classSummary = demoMode ? DEMO_CLASS_SUMMARY : (summaryData?.class_summaries || DEMO_CLASS_SUMMARY);

  const filteredInvoices = invoices.filter((inv: Invoice) =>
    inv.student_name.toLowerCase().includes(search.toLowerCase()) ||
    inv.class_name.toLowerCase().includes(search.toLowerCase())
  );

  const stats = useMemo(() => {
    const totalCollected = classSummary.reduce((sum: number, c: any) => sum + c.collected, 0);
    const totalFees = classSummary.reduce((sum: number, c: any) => sum + c.total, 0);
    return {
      totalCollected,
      totalPending: totalFees - totalCollected,
      collectionRate: totalFees > 0 ? ((totalCollected / totalFees) * 100) : 0,
      overdue: invoices.filter((i: Invoice) => i.status === "overdue").length,
    };
  }, [classSummary, invoices]);

  const handleSendReminder = async (invoiceId: string) => {
    if (demoMode) {
      toast({ title: "Reminder sent", description: "Payment reminder sent to parent" });
      return;
    }
    try {
      await financeApi.sendReminder(invoiceId);
      toast({ title: "Reminder sent" });
    } catch {
      toast({ title: "Failed to send reminder", variant: "destructive" });
    }
  };

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
          {!demoMode && (
            <Button variant="outline" size="sm" onClick={() => refetchInvoices()}>
              <RefreshCw className="h-4 w-4 mr-1" /> Refresh
            </Button>
          )}
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" /> Create Invoice
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Collected", value: formatCurrency(stats.totalCollected), icon: DollarSign, color: "text-emerald-600" },
          { label: "Pending", value: formatCurrency(stats.totalPending), icon: Clock, color: "text-amber-600" },
          { label: "Collection Rate", value: `${stats.collectionRate.toFixed(1)}%`, icon: TrendingUp, color: "text-blue-600" },
          { label: "Overdue", value: stats.overdue, icon: AlertCircle, color: "text-red-600" },
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

      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
          <TabsTrigger value="payments">Payments</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Fee Collection by Class</CardTitle>
              <CardDescription>Collection progress across classes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {classSummary.map((item: any) => {
                  const pct = item.total > 0 ? (item.collected / item.total) * 100 : 0;
                  return (
                    <div key={item.class_name} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{item.class_name}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-muted-foreground">
                            {formatCurrency(item.collected)} / {formatCurrency(item.total)}
                          </span>
                          <Badge variant={pct >= 80 ? "default" : pct >= 60 ? "secondary" : "destructive"}>
                            {pct.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                      <Progress value={pct} className="h-2" />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoices */}
        <TabsContent value="invoices" className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search student..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-border bg-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Student</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[60px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInvoices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">No invoices found</TableCell>
                  </TableRow>
                ) : (
                  filteredInvoices.map((inv: Invoice, i: number) => (
                    <motion.tr key={inv.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
                      className="border-b border-border hover:bg-muted/30 transition-colors">
                      <TableCell className="font-medium text-sm">{inv.student_name}</TableCell>
                      <TableCell className="text-sm">{inv.class_name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{inv.description}</TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(inv.amount)}</TableCell>
                      <TableCell className="text-sm">{inv.due_date}</TableCell>
                      <TableCell>
                        <Badge className={cn("gap-1", STATUS_CONFIG[inv.status].bg, STATUS_CONFIG[inv.status].color)}>
                          {STATUS_CONFIG[inv.status].label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem><FileText className="h-3.5 w-3.5 mr-2" /> View</DropdownMenuItem>
                            {inv.status !== "paid" && (
                              <>
                                <DropdownMenuItem><CreditCard className="h-3.5 w-3.5 mr-2" /> Record Payment</DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleSendReminder(inv.id)}>
                                  <Send className="h-3.5 w-3.5 mr-2" /> Send Reminder
                                </DropdownMenuItem>
                              </>
                            )}
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

        {/* Payments */}
        <TabsContent value="payments" className="space-y-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-border bg-card overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40">
                  <TableHead>Student</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Reference</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.map((pay: Payment, i: number) => (
                  <motion.tr key={pay.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
                    className="border-b border-border hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium text-sm">{pay.student_name}</TableCell>
                    <TableCell className="text-right font-medium text-emerald-600">{formatCurrency(pay.amount)}</TableCell>
                    <TableCell className="text-sm">{pay.payment_date}</TableCell>
                    <TableCell><Badge variant="secondary">{pay.method}</Badge></TableCell>
                    <TableCell className="text-sm font-mono text-muted-foreground">{pay.reference_no}</TableCell>
                  </motion.tr>
                ))}
              </TableBody>
            </Table>
          </motion.div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FinancePage;
