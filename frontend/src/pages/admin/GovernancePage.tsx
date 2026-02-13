import { useState } from "react";
import { motion } from "framer-motion";
import { Shield, FileText, Download, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const GovernancePage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data
  const auditLogs = [
    { id: 1, timestamp: "2024-02-13 14:30:25", user: "admin@school.edu", action: "User Created", resource: "student@demo.school", ipAddress: "192.168.1.100" },
    { id: 2, timestamp: "2024-02-13 14:25:10", user: "teacher@school.edu", action: "Grade Updated", resource: "Assignment #45", ipAddress: "192.168.1.105" },
    { id: 3, timestamp: "2024-02-13 14:20:05", user: "admin@school.edu", action: "Permission Changed", resource: "teacher@demo.school", ipAddress: "192.168.1.100" },
  ];

  const consents = [
    { id: 1, student: "John Doe", parent: "Michael Doe", type: "Data Processing", status: "Granted", date: "2024-01-15" },
    { id: 2, student: "Jane Smith", parent: "Sarah Smith", type: "Photo/Video", status: "Granted", date: "2024-01-16" },
    { id: 3, student: "Alex Chen", parent: "Maria Chen", type: "Medical Treatment", status: "Pending", date: "2024-02-10" },
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
              <Shield className="h-8 w-8 text-primary" />
              Governance & Compliance
            </h1>
            <p className="text-muted-foreground mt-1">Audit logs, consents, and compliance tracking</p>
          </div>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Audit Logs</CardDescription>
              <CardTitle className="text-3xl">15,234</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Consents</CardDescription>
              <CardTitle className="text-3xl">450</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Pending Consents</CardDescription>
              <CardTitle className="text-3xl">12</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Compliance Score</CardDescription>
              <CardTitle className="text-3xl">98%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="audit" className="space-y-4">
          <TabsList>
            <TabsTrigger value="audit">Audit Logs</TabsTrigger>
            <TabsTrigger value="consents">Consents</TabsTrigger>
            <TabsTrigger value="access">Data Access</TabsTrigger>
            <TabsTrigger value="reports">Compliance Reports</TabsTrigger>
          </TabsList>

          <TabsContent value="audit" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Immutable Audit Trail</CardTitle>
                    <CardDescription>All system actions are logged and cannot be modified</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search logs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 w-64"
                      />
                    </div>
                    <Button variant="outline" size="icon">
                      <Filter className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>IP Address</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-mono text-sm">{log.timestamp}</TableCell>
                        <TableCell>{log.user}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{log.action}</Badge>
                        </TableCell>
                        <TableCell>{log.resource}</TableCell>
                        <TableCell className="font-mono text-sm">{log.ipAddress}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="consents" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Consent Management</CardTitle>
                <CardDescription>GDPR and child protection consent tracking</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student</TableHead>
                      <TableHead>Parent/Guardian</TableHead>
                      <TableHead>Consent Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {consents.map((consent) => (
                      <TableRow key={consent.id}>
                        <TableCell className="font-medium">{consent.student}</TableCell>
                        <TableCell>{consent.parent}</TableCell>
                        <TableCell>{consent.type}</TableCell>
                        <TableCell>
                          <Badge variant={consent.status === "Granted" ? "default" : "secondary"}>
                            {consent.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{consent.date}</TableCell>
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

          <TabsContent value="access" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Data Access Tracking</CardTitle>
                <CardDescription>Monitor who accessed what data and when</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Data access tracking interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Compliance Reports</CardTitle>
                <CardDescription>Generate inspection-ready compliance reports</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="border-2">
                    <CardHeader>
                      <CardTitle className="text-lg">GDPR Compliance Report</CardTitle>
                      <CardDescription>Data protection and privacy compliance</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full">
                        <FileText className="h-4 w-4 mr-2" />
                        Generate Report
                      </Button>
                    </CardContent>
                  </Card>
                  <Card className="border-2">
                    <CardHeader>
                      <CardTitle className="text-lg">Child Protection Report</CardTitle>
                      <CardDescription>Safeguarding and consent records</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full">
                        <FileText className="h-4 w-4 mr-2" />
                        Generate Report
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default GovernancePage;
