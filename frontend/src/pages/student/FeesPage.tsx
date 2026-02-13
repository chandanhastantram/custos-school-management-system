import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { DollarSign, CreditCard, Download, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { studentApi } from "@/services/student-api";
import { useAuthStore } from "@/stores/auth-store";
import { toast } from "@/hooks/use-toast";

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
  }).format(amount);
};

const FeesPage = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  // Fetch fees
  const { data: fees = [], isLoading, refetch } = useQuery({
    queryKey: ["fees", user?.id],
    queryFn: () => studentApi.getFees(user?.id || ""),
    enabled: !!user?.id,
    retry: 1,
  });

  // Pay fee mutation
  const payFeeMutation = useMutation({
    mutationFn: ({ feeId, amount }: { feeId: string; amount: number }) =>
      studentApi.payFee(feeId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fees"] });
      toast({ title: "Payment initiated successfully" });
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Calculate stats
  const pendingFees = fees.filter(f => f.status === "pending");
  const totalPending = pendingFees.reduce((sum, f) => sum + f.amount, 0);
  const paidFees = fees.filter(f => f.status === "paid");
  const totalPaid = paidFees.reduce((sum, f) => sum + (f.paid_amount || 0), 0);
  const nextDueDate = pendingFees[0]?.due_date || "N/A";

  const handlePayNow = (feeId: string, amount: number) => {
    if (confirm(`Pay ${formatCurrency(amount)}?`)) {
      payFeeMutation.mutate({ feeId, amount });
    }
  };

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <DollarSign className="h-8 w-8 text-primary" />
              Fees & Payments
            </h1>
            <p className="text-muted-foreground mt-1">Manage your fee payments and view history</p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Alert for pending payments */}
        {pendingFees.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Payment Due</AlertTitle>
            <AlertDescription>
              You have {pendingFees.length} pending invoice{pendingFees.length > 1 ? 's' : ''} totaling {formatCurrency(totalPending)}. Please pay before the due date to avoid late fees.
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Pending</CardDescription>
              <CardTitle className="text-3xl text-destructive">{formatCurrency(totalPending)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Paid This Year</CardDescription>
              <CardTitle className="text-3xl">{formatCurrency(totalPaid)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Next Due Date</CardDescription>
              <CardTitle className="text-lg">{nextDueDate !== "N/A" ? new Date(nextDueDate).toLocaleDateString() : "N/A"}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Payment Status</CardDescription>
              <CardTitle className="text-lg text-green-600">
                {pendingFees.length === 0 ? "All Clear" : "Pending"}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="pending" className="space-y-4">
          <TabsList>
            <TabsTrigger value="pending">Pending Invoices</TabsTrigger>
            <TabsTrigger value="history">Payment History</TabsTrigger>
          </TabsList>

          <TabsContent value="pending">
            <Card>
              <CardHeader>
                <CardTitle>Pending Invoices</CardTitle>
                <CardDescription>Pay your outstanding fees</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : pendingFees.length === 0 ? (
                  <p className="text-center py-12 text-muted-foreground">No pending invoices</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingFees.map((fee) => (
                        <TableRow key={fee.id}>
                          <TableCell className="font-medium">{fee.fee_type}</TableCell>
                          <TableCell className="text-lg font-semibold">{formatCurrency(fee.amount)}</TableCell>
                          <TableCell>{new Date(fee.due_date).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Badge variant={fee.status === "overdue" ? "destructive" : "secondary"}>
                              {fee.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button 
                              size="sm" 
                              onClick={() => handlePayNow(fee.id, fee.amount)}
                              disabled={payFeeMutation.isPending}
                            >
                              {payFeeMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                              <CreditCard className="h-4 w-4 mr-2" />
                              Pay Now
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>Payment History</CardTitle>
                <CardDescription>View your past payments</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : paidFees.length === 0 ? (
                  <p className="text-center py-12 text-muted-foreground">No payment history</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Paid Date</TableHead>
                        <TableHead>Method</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paidFees.map((fee) => (
                        <TableRow key={fee.id}>
                          <TableCell className="font-medium">{fee.fee_type}</TableCell>
                          <TableCell>{formatCurrency(fee.paid_amount || 0)}</TableCell>
                          <TableCell>{fee.paid_date ? new Date(fee.paid_date).toLocaleDateString() : "-"}</TableCell>
                          <TableCell>Online</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">
                              <Download className="h-4 w-4 mr-2" />
                              Receipt
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default FeesPage;
