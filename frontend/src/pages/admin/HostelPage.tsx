import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { 
  Building2, Bed, Users, Plus, Search, Filter, Edit, Trash2, 
  MoreHorizontal, Loader2, AlertCircle, UserPlus, RefreshCw 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { hostelApi, type Hostel, type Room, type Warden } from "@/services/hostel-api";

const HostelPage = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [hostelDialogOpen, setHostelDialogOpen] = useState(false);
  const [roomDialogOpen, setRoomDialogOpen] = useState(false);
  const [wardenDialogOpen, setWardenDialogOpen] = useState(false);
  const [editingHostel, setEditingHostel] = useState<Hostel | null>(null);
  const [selectedHostelId, setSelectedHostelId] = useState<string | null>(null);

  // Fetch hostels
  const { data: hostels = [], isLoading: hostelsLoading, refetch: refetchHostels } = useQuery({
    queryKey: ["hostels"],
    queryFn: () => hostelApi.getHostels(),
    retry: 1,
  });

  // Fetch rooms for selected hostel
  const { data: rooms = [] } = useQuery({
    queryKey: ["rooms", selectedHostelId],
    queryFn: () => selectedHostelId ? hostelApi.getRooms(selectedHostelId) : Promise.resolve([]),
    enabled: !!selectedHostelId,
  });

  // Fetch wardens
  const { data: wardens = [], refetch: refetchWardens } = useQuery({
    queryKey: ["wardens"],
    queryFn: () => hostelApi.getWardens(),
  });

  // Fetch occupancy stats
  const { data: occupancyData } = useQuery({
    queryKey: ["occupancy"],
    queryFn: () => hostelApi.getOccupancy(),
  });

  // Hostel mutations
  const createHostelMutation = useMutation({
    mutationFn: hostelApi.createHostel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostels"] });
      queryClient.invalidateQueries({ queryKey: ["occupancy"] });
      toast({ title: "Hostel created successfully" });
      setHostelDialogOpen(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const updateHostelMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Hostel> }) =>
      hostelApi.updateHostel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostels"] });
      toast({ title: "Hostel updated successfully" });
      setHostelDialogOpen(false);
      setEditingHostel(null);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const deleteHostelMutation = useMutation({
    mutationFn: hostelApi.deleteHostel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostels"] });
      queryClient.invalidateQueries({ queryKey: ["occupancy"] });
      toast({ title: "Hostel deleted", variant: "destructive" });
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Room mutations
  const createRoomMutation = useMutation({
    mutationFn: hostelApi.createRoom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms"] });
      queryClient.invalidateQueries({ queryKey: ["hostels"] });
      toast({ title: "Room created successfully" });
      setRoomDialogOpen(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  const deleteRoomMutation = useMutation({
    mutationFn: hostelApi.deleteRoom,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms"] });
      queryClient.invalidateQueries({ queryKey: ["hostels"] });
      toast({ title: "Room deleted", variant: "destructive" });
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Warden mutations
  const createWardenMutation = useMutation({
    mutationFn: hostelApi.createWarden,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wardens"] });
      toast({ title: "Warden added successfully" });
      setWardenDialogOpen(false);
    },
    onError: (error: any) => {
      toast({ title: "Error", description: error.message, variant: "destructive" });
    },
  });

  // Handlers
  const handleCreateHostel = () => {
    setEditingHostel(null);
    setHostelDialogOpen(true);
  };

  const handleEditHostel = (hostel: Hostel) => {
    setEditingHostel(hostel);
    setHostelDialogOpen(true);
  };

  const handleDeleteHostel = (id: string) => {
    if (confirm("Are you sure you want to delete this hostel?")) {
      deleteHostelMutation.mutate(id);
    }
  };

  const handleSaveHostel = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get("name") as string,
      code: formData.get("code") as string,
      gender: formData.get("gender") as "male" | "female" | "mixed",
      total_capacity: parseInt(formData.get("capacity") as string),
      address: formData.get("address") as string,
      contact_number: formData.get("contact") as string,
      is_active: true,
    };

    if (editingHostel) {
      updateHostelMutation.mutate({ id: editingHostel.id, data });
    } else {
      createHostelMutation.mutate(data);
    }
  };

  const handleCreateRoom = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedHostelId) return;
    
    const formData = new FormData(e.currentTarget);
    const data = {
      hostel_id: selectedHostelId,
      room_number: formData.get("room_number") as string,
      floor: parseInt(formData.get("floor") as string),
      capacity: parseInt(formData.get("capacity") as string),
      is_active: true,
    };

    createRoomMutation.mutate(data);
  };

  const handleCreateWarden = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get("name") as string,
      phone: formData.get("phone") as string,
      email: formData.get("email") as string,
      is_chief_warden: formData.get("is_chief") === "true",
      is_active: true,
    };

    createWardenMutation.mutate(data);
  };

  // Calculate stats
  const totalHostels = hostels.length;
  const totalRooms = hostels.reduce((sum, h) => sum + (h.rooms_count || 0), 0);
  const occupiedBeds = hostels.reduce((sum, h) => sum + (h.occupied_beds || 0), 0);
  const totalCapacity = hostels.reduce((sum, h) => sum + h.total_capacity, 0);
  const occupancyRate = totalCapacity > 0 ? Math.round((occupiedBeds / totalCapacity) * 100) : 0;

  // Filter hostels
  const filteredHostels = hostels.filter(h =>
    h.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    h.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetchHostels()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={handleCreateHostel}>
              <Plus className="h-4 w-4 mr-2" />
              Add Hostel
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Hostels</CardDescription>
              <CardTitle className="text-3xl">{totalHostels}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Rooms</CardDescription>
              <CardTitle className="text-3xl">{totalRooms}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Occupied Beds</CardDescription>
              <CardTitle className="text-3xl">{occupiedBeds}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Occupancy Rate</CardDescription>
              <CardTitle className="text-3xl">{occupancyRate}%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="hostels" className="space-y-4">
          <TabsList>
            <TabsTrigger value="hostels">Hostels</TabsTrigger>
            <TabsTrigger value="rooms">Rooms</TabsTrigger>
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
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {hostelsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : filteredHostels.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Building2 className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No hostels found</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredHostels.map((hostel) => (
                      <Card key={hostel.id} className="border-2">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <CardTitle className="text-lg">{hostel.name}</CardTitle>
                              <CardDescription>
                                {hostel.code} • {hostel.gender} • {hostel.rooms_count || 0} rooms
                              </CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={
                                (hostel.occupied_beds || 0) / hostel.total_capacity > 0.9 
                                  ? "destructive" 
                                  : "default"
                              }>
                                {Math.round(((hostel.occupied_beds || 0) / hostel.total_capacity) * 100)}% Full
                              </Badge>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon" className="h-8 w-8">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => handleEditHostel(hostel)}>
                                    <Edit className="h-3.5 w-3.5 mr-2" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => setSelectedHostelId(hostel.id)}>
                                    <Bed className="h-3.5 w-3.5 mr-2" />
                                    View Rooms
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem 
                                    onClick={() => handleDeleteHostel(hostel.id)}
                                    className="text-destructive focus:text-destructive"
                                  >
                                    <Trash2 className="h-3.5 w-3.5 mr-2" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Occupied Beds</span>
                              <span className="font-medium">
                                {hostel.occupied_beds || 0} / {hostel.total_capacity}
                              </span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                              <div
                                className="bg-primary h-2 rounded-full transition-all"
                                style={{ 
                                  width: `${((hostel.occupied_beds || 0) / hostel.total_capacity) * 100}%` 
                                }}
                              />
                            </div>
                            {hostel.contact_number && (
                              <p className="text-xs text-muted-foreground mt-2">
                                📞 {hostel.contact_number}
                              </p>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rooms" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Rooms</CardTitle>
                    <CardDescription>
                      {selectedHostelId 
                        ? `Viewing rooms for ${hostels.find(h => h.id === selectedHostelId)?.name}`
                        : "Select a hostel to view rooms"
                      }
                    </CardDescription>
                  </div>
                  {selectedHostelId && (
                    <Button onClick={() => setRoomDialogOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Room
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {!selectedHostelId ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Bed className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>Select a hostel from the Hostels tab to view rooms</p>
                  </div>
                ) : rooms.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <p>No rooms found for this hostel</p>
                    <Button className="mt-4" onClick={() => setRoomDialogOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add First Room
                    </Button>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Room Number</TableHead>
                        <TableHead>Floor</TableHead>
                        <TableHead>Capacity</TableHead>
                        <TableHead>Occupied</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="w-[60px]" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rooms.map((room) => (
                        <TableRow key={room.id}>
                          <TableCell className="font-medium">{room.room_number}</TableCell>
                          <TableCell>Floor {room.floor}</TableCell>
                          <TableCell>{room.capacity} beds</TableCell>
                          <TableCell>{room.occupied_beds || 0} / {room.capacity}</TableCell>
                          <TableCell>
                            <Badge variant={room.is_active ? "default" : "secondary"}>
                              {room.is_active ? "Active" : "Inactive"}
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
                                  <Edit className="h-3.5 w-3.5 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem 
                                  onClick={() => deleteRoomMutation.mutate(room.id)}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="h-3.5 w-3.5 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="wardens" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Hostel Wardens</CardTitle>
                    <CardDescription>Manage warden assignments</CardDescription>
                  </div>
                  <Button onClick={() => setWardenDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Warden
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {wardens.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Users className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No wardens assigned yet</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Phone</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Assigned Hostel</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead className="w-[60px]" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {wardens.map((warden) => (
                        <TableRow key={warden.id}>
                          <TableCell className="font-medium">{warden.name}</TableCell>
                          <TableCell>{warden.phone}</TableCell>
                          <TableCell>{warden.email || "-"}</TableCell>
                          <TableCell>{warden.hostel_name || "Not assigned"}</TableCell>
                          <TableCell>
                            <Badge variant={warden.is_chief_warden ? "default" : "secondary"}>
                              {warden.is_chief_warden ? "Chief Warden" : "Warden"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
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

        {/* Hostel Dialog */}
        <Dialog open={hostelDialogOpen} onOpenChange={setHostelDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingHostel ? "Edit Hostel" : "Add New Hostel"}</DialogTitle>
              <DialogDescription>
                {editingHostel ? "Update hostel information" : "Create a new hostel building"}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSaveHostel}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Hostel Name</Label>
                  <Input 
                    id="name" 
                    name="name" 
                    defaultValue={editingHostel?.name}
                    placeholder="e.g., Boys Hostel A" 
                    required 
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="code">Code</Label>
                    <Input 
                      id="code" 
                      name="code" 
                      defaultValue={editingHostel?.code}
                      placeholder="e.g., BH-A" 
                      required 
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="gender">Gender</Label>
                    <Select name="gender" defaultValue={editingHostel?.gender || "male"}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="mixed">Mixed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="capacity">Total Capacity</Label>
                  <Input 
                    id="capacity" 
                    name="capacity" 
                    type="number" 
                    defaultValue={editingHostel?.total_capacity}
                    placeholder="e.g., 150" 
                    required 
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="address">Address</Label>
                  <Input 
                    id="address" 
                    name="address" 
                    defaultValue={editingHostel?.address}
                    placeholder="Building address" 
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="contact">Contact Number</Label>
                  <Input 
                    id="contact" 
                    name="contact" 
                    defaultValue={editingHostel?.contact_number}
                    placeholder="+91 1234567890" 
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setHostelDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createHostelMutation.isPending || updateHostelMutation.isPending}>
                  {(createHostelMutation.isPending || updateHostelMutation.isPending) && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  {editingHostel ? "Update" : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Room Dialog */}
        <Dialog open={roomDialogOpen} onOpenChange={setRoomDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Room</DialogTitle>
              <DialogDescription>Create a new room in the selected hostel</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateRoom}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="room_number">Room Number</Label>
                  <Input id="room_number" name="room_number" placeholder="e.g., 101" required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="floor">Floor</Label>
                    <Input id="floor" name="floor" type="number" placeholder="e.g., 1" required />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="capacity">Capacity</Label>
                    <Input id="capacity" name="capacity" type="number" placeholder="e.g., 3" required />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setRoomDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createRoomMutation.isPending}>
                  {createRoomMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Room
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Warden Dialog */}
        <Dialog open={wardenDialogOpen} onOpenChange={setWardenDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Warden</DialogTitle>
              <DialogDescription>Add a new warden to the system</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateWarden}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" name="name" placeholder="Full name" required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" name="phone" placeholder="+91 1234567890" required />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" name="email" type="email" placeholder="email@example.com" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="is_chief">Role</Label>
                  <Select name="is_chief" defaultValue="false">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="false">Warden</SelectItem>
                      <SelectItem value="true">Chief Warden</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setWardenDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createWardenMutation.isPending}>
                  {createWardenMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Add Warden
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </motion.div>
    </div>
  );
};

export default HostelPage;
