import { useState } from "react";
import { motion } from "framer-motion";
import { Users, DollarSign, Calendar, FileText, Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const HRPayrollPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data
  const employees = [
    { id: 1, name: "Dr. Sarah Johnson", role: "Principal", department: "Administration", salary: "$8,500", status: "Active" },
    { id: 2, name: "James Wilson", role: "Teacher", department: "Mathematics", salary: "$4,200", status: "Active" },
    { id: 3, name: "Emily Brown", role: "Teacher", department: "Science", salary: "$4,000", status: "On Leave" },
  ];

  const payrollHistory = [
    { id: 1, month: "January 2024", processed: "2024-01-31", totalAmount: "$125,000", employees: 45, status: "Completed" },
    { id: 2, month: "December 2023", processed: "2023-12-31", totalAmount: "$122,500", employees: 44, status: "Completed" },
  ];

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
              <Users className="h-8 w-8 text-primary" />
              HR & Payroll
            </h1>
            <p className="text-muted-foreground mt-1">Manage employees, payroll, and leave requests</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Employee
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Employees</CardDescription>
              <CardTitle className="text-3xl">45</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Monthly Payroll</CardDescription>
              <CardTitle className="text-3xl">$125K</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>On Leave</CardDescription>
              <CardTitle className="text-3xl">3</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Pending Approvals</CardDescription>
              <CardTitle className="text-3xl">7</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="employees" className="space-y-4">
          <TabsList>
            <TabsTrigger value="employees">Employees</TabsTrigger>
            <TabsTrigger value="payroll">Payroll</TabsTrigger>
            <TabsTrigger value="leaves">Leave Management</TabsTrigger>
            <TabsTrigger value="departments">Departments</TabsTrigger>
          </TabsList>

          <TabsContent value="employees" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Employee Directory</CardTitle>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search employees..."
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
                      <TableHead>Name</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Salary</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {employees.map((employee) => (
                      <TableRow key={employee.id}>
                        <TableCell className="font-medium">{employee.name}</TableCell>
                        <TableCell>{employee.role}</TableCell>
                        <TableCell>{employee.department}</TableCell>
                        <TableCell>{employee.salary}</TableCell>
                        <TableCell>
                          <Badge variant={employee.status === "Active" ? "default" : "secondary"}>
                            {employee.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">View</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="payroll" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Payroll History</CardTitle>
                    <CardDescription>View and process monthly payroll</CardDescription>
                  </div>
                  <Button>
                    <DollarSign className="h-4 w-4 mr-2" />
                    Process Payroll
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Month</TableHead>
                      <TableHead>Processed Date</TableHead>
                      <TableHead>Total Amount</TableHead>
                      <TableHead>Employees</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payrollHistory.map((payroll) => (
                      <TableRow key={payroll.id}>
                        <TableCell className="font-medium">{payroll.month}</TableCell>
                        <TableCell>{payroll.processed}</TableCell>
                        <TableCell>{payroll.totalAmount}</TableCell>
                        <TableCell>{payroll.employees}</TableCell>
                        <TableCell>
                          <Badge variant="default">{payroll.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">View Details</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="leaves" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Leave Requests</CardTitle>
                <CardDescription>Manage employee leave applications</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Leave management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="departments" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Departments</CardTitle>
                <CardDescription>Manage organizational departments</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Department management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default HRPayrollPage;
