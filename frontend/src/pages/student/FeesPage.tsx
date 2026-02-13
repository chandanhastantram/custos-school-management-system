import { useState } from "react";
import { motion } from "framer-motion";
import { DollarSign, CreditCard, Download, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const FeesPage = () => {
  const pendingInvoices = [
    { id: 1, description: "Tuition Fee - Q1 2024", amount: "$2,500", dueDate: "2024-02-28", status: "Pending" },
    { id: 2, description: "Library Fee", amount: "$150", dueDate: "2024-03-15", status: "Pending" },
  ];

  const paymentHistory = [
    { id: 3, description: "Tuition Fee - Q4 2023", amount: "$2,500", paidDate: "2023-12-15", method: "Credit Card", receipt: "RCP-2023-1215" },
  ];

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <DollarSign className="h-8 w-8 text-primary" />
            Fees & Payments
          </h1>
          <p className="text-muted-foreground mt-1">Manage your fee payments and view history</p>
        </div>

        {/* Alert for pending payments */}
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Payment Due</AlertTitle>
          <AlertDescription>
            You have 2 pending invoices totaling $2,650. Please pay before the due date to avoid late fees.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Pending</CardDescription>
              <CardTitle className="text-3xl text-destructive">$2,650</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Paid This Year</CardDescription>
              <CardTitle className="text-3xl">$7,500</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Next Due Date</CardDescription>
              <CardTitle className="text-lg">Feb 28, 2024</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Payment Status</CardDescription>
              <CardTitle className="text-lg text-green-600">Good Standing</CardTitle>
            </CardHeader>
          </Card>
        </div>

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
                    {pendingInvoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-medium">{invoice.description}</TableCell>
                        <TableCell className="text-lg font-semibold">{invoice.amount}</TableCell>
                        <TableCell>{invoice.dueDate}</TableCell>
                        <TableCell>
                          <Badge variant="destructive">{invoice.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button size="sm">
                            <CreditCard className="h-4 w-4 mr-2" />
                            Pay Now
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
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
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Paid Date</TableHead>
                      <TableHead>Method</TableHead>
                      <TableHead>Receipt</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paymentHistory.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell className="font-medium">{payment.description}</TableCell>
                        <TableCell>{payment.amount}</TableCell>
                        <TableCell>{payment.paidDate}</TableCell>
                        <TableCell>{payment.method}</TableCell>
                        <TableCell className="font-mono text-sm">{payment.receipt}</TableCell>
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
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default FeesPage;
