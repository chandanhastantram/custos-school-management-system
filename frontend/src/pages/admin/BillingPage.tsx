import { useState } from "react";
import { motion } from "framer-motion";
import { CreditCard, Download, TrendingUp, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const BillingPage = () => {
  const currentPlan = {
    name: "Professional",
    price: "$299",
    period: "per month",
    students: 500,
    maxStudents: 1000,
    features: ["Unlimited Users", "Advanced Analytics", "Priority Support", "Custom Branding"],
    nextBilling: "2024-03-15"
  };

  const invoices = [
    { id: 1, date: "2024-02-01", amount: "$299", status: "Paid", invoice: "INV-2024-02" },
    { id: 2, date: "2024-01-01", amount: "$299", status: "Paid", invoice: "INV-2024-01" },
  ];

  const plans = [
    { name: "Starter", price: "$99", students: 250, features: ["Basic Features", "Email Support"] },
    { name: "Professional", price: "$299", students: 1000, features: ["All Starter", "Advanced Analytics", "Priority Support"], current: true },
    { name: "Enterprise", price: "$599", students: 5000, features: ["All Professional", "Custom Integration", "Dedicated Manager"] },
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
              <CreditCard className="h-8 w-8 text-primary" />
              Billing & Subscription
            </h1>
            <p className="text-muted-foreground mt-1">Manage your subscription and billing</p>
          </div>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download Invoice
          </Button>
        </div>

        {/* Current Plan Card */}
        <Card className="border-2 border-primary">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl">{currentPlan.name} Plan</CardTitle>
                <CardDescription className="text-lg mt-1">
                  <span className="text-3xl font-bold text-foreground">{currentPlan.price}</span>
                  <span className="text-muted-foreground"> {currentPlan.period}</span>
                </CardDescription>
              </div>
              <Badge className="text-sm">Current Plan</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Student Usage</span>
                  <span className="font-medium">{currentPlan.students} / {currentPlan.maxStudents}</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full"
                    style={{ width: `${(currentPlan.students / currentPlan.maxStudents) * 100}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {currentPlan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Next Billing Date</AlertTitle>
                <AlertDescription>
                  Your next payment of {currentPlan.price} will be charged on {currentPlan.nextBilling}
                </AlertDescription>
              </Alert>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">Change Plan</Button>
                <Button variant="outline" className="flex-1">Update Payment Method</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="invoices" className="space-y-4">
          <TabsList>
            <TabsTrigger value="invoices">Invoices</TabsTrigger>
            <TabsTrigger value="plans">Available Plans</TabsTrigger>
            <TabsTrigger value="payment">Payment Method</TabsTrigger>
          </TabsList>

          <TabsContent value="invoices">
            <Card>
              <CardHeader>
                <CardTitle>Billing History</CardTitle>
                <CardDescription>View and download past invoices</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-mono">{invoice.invoice}</TableCell>
                        <TableCell>{invoice.date}</TableCell>
                        <TableCell className="font-semibold">{invoice.amount}</TableCell>
                        <TableCell>
                          <Badge variant="default">{invoice.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="plans">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plans.map((plan) => (
                <Card key={plan.name} className={plan.current ? "border-2 border-primary" : ""}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle>{plan.name}</CardTitle>
                        <CardDescription className="text-2xl font-bold text-foreground mt-2">
                          {plan.price}
                          <span className="text-sm font-normal text-muted-foreground">/month</span>
                        </CardDescription>
                      </div>
                      {plan.current && <Badge>Current</Badge>}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">Up to {plan.students} students</p>
                      <div className="space-y-2">
                        {plan.features.map((feature, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            <span className="text-green-500">✓</span>
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>
                      <Button className="w-full" variant={plan.current ? "outline" : "default"}>
                        {plan.current ? "Current Plan" : "Upgrade"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="payment">
            <Card>
              <CardHeader>
                <CardTitle>Payment Method</CardTitle>
                <CardDescription>Manage your payment information</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-4 border rounded-lg">
                    <CreditCard className="h-8 w-8" />
                    <div className="flex-1">
                      <p className="font-medium">Visa ending in 4242</p>
                      <p className="text-sm text-muted-foreground">Expires 12/2025</p>
                    </div>
                    <Badge>Default</Badge>
                  </div>
                  <Button variant="outline">Add Payment Method</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default BillingPage;
