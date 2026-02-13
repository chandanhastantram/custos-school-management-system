import { useState } from "react";
import { motion } from "framer-motion";
import { Building2, Bed, Users, Plus, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const HostelPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data
  const hostels = [
    { id: 1, name: "Boys Hostel A", floors: 3, totalRooms: 45, occupiedBeds: 120, totalBeds: 135 },
    { id: 2, name: "Girls Hostel B", floors: 4, totalRooms: 60, occupiedBeds: 150, totalBeds: 180 },
  ];

  const allocations = [
    { id: 1, studentName: "John Doe", hostel: "Boys Hostel A", room: "101", bed: "A", checkIn: "2024-01-15" },
    { id: 2, studentName: "Jane Smith", hostel: "Girls Hostel B", room: "205", bed: "B", checkIn: "2024-01-16" },
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
              <Building2 className="h-8 w-8 text-primary" />
              Hostel Management
            </h1>
            <p className="text-muted-foreground mt-1">Manage hostels, rooms, and student allocations</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Hostel
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Hostels</CardDescription>
              <CardTitle className="text-3xl">2</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Rooms</CardDescription>
              <CardTitle className="text-3xl">105</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Occupied Beds</CardDescription>
              <CardTitle className="text-3xl">270</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Occupancy Rate</CardDescription>
              <CardTitle className="text-3xl">86%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="hostels" className="space-y-4">
          <TabsList>
            <TabsTrigger value="hostels">Hostels</TabsTrigger>
            <TabsTrigger value="allocations">Allocations</TabsTrigger>
            <TabsTrigger value="wardens">Wardens</TabsTrigger>
          </TabsList>

          <TabsContent value="hostels" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Hostel Buildings</CardTitle>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search hostels..."
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {hostels.map((hostel) => (
                    <Card key={hostel.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{hostel.name}</CardTitle>
                            <CardDescription>{hostel.floors} floors • {hostel.totalRooms} rooms</CardDescription>
                          </div>
                          <Badge variant={hostel.occupiedBeds / hostel.totalBeds > 0.9 ? "destructive" : "default"}>
                            {Math.round((hostel.occupiedBeds / hostel.totalBeds) * 100)}% Full
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Occupied Beds</span>
                            <span className="font-medium">{hostel.occupiedBeds} / {hostel.totalBeds}</span>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full"
                              style={{ width: `${(hostel.occupiedBeds / hostel.totalBeds) * 100}%` }}
                            />
                          </div>
                          <div className="flex gap-2 mt-4">
                            <Button variant="outline" size="sm" className="flex-1">View Rooms</Button>
                            <Button size="sm" className="flex-1">Allocate</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="allocations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Student Allocations</CardTitle>
                <CardDescription>View and manage student hostel assignments</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student Name</TableHead>
                      <TableHead>Hostel</TableHead>
                      <TableHead>Room</TableHead>
                      <TableHead>Bed</TableHead>
                      <TableHead>Check-in Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {allocations.map((allocation) => (
                      <TableRow key={allocation.id}>
                        <TableCell className="font-medium">{allocation.studentName}</TableCell>
                        <TableCell>{allocation.hostel}</TableCell>
                        <TableCell>{allocation.room}</TableCell>
                        <TableCell>{allocation.bed}</TableCell>
                        <TableCell>{allocation.checkIn}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">Edit</Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="wardens" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Hostel Wardens</CardTitle>
                <CardDescription>Manage warden assignments</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Warden management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default HostelPage;
