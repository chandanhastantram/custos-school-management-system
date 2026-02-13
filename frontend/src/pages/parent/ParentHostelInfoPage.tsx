import { useState } from "react";
import { motion } from "framer-motion";
import { Home, User, Phone, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const ParentHostelInfoPage = () => {
  const [selectedChild, setSelectedChild] = useState("1");

  const children = [
    { id: "1", name: "John Doe", class: "10-A", hostel: "Boys Hostel A", room: "201" },
    { id: "2", name: "Jane Doe", class: "8-B", hostel: null, room: null },
  ];

  const selectedChildData = children.find(c => c.id === selectedChild);

  const hostelInfo = {
    name: "Boys Hostel A",
    building: "Block A",
    roomNo: "201",
    floor: "2nd Floor",
    roomType: "Shared (4 students)",
    warden: {
      name: "Mr. David Johnson",
      phone: "+1 234-567-8901",
      email: "david.johnson@school.com"
    },
    roommates: [
      { name: "Alex Chen", class: "10-A" },
      { name: "Mike Wilson", class: "10-B" },
      { name: "Tom Brown", class: "10-A" },
    ],
    facilities: [
      "24/7 Security",
      "WiFi Access",
      "Study Room",
      "Common Room",
      "Laundry Service",
      "Mess Facility"
    ]
  };

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
              <Home className="h-8 w-8 text-primary" />
              Hostel Information
            </h1>
            <p className="text-muted-foreground mt-1">View your child&apos;s hostel details</p>
          </div>
          <Select value={selectedChild} onValueChange={setSelectedChild}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select child" />
            </SelectTrigger>
            <SelectContent>
              {children.map((child) => (
                <SelectItem key={child.id} value={child.id}>
                  {child.name} - {child.hostel || "Day Scholar"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedChildData && selectedChildData.hostel ? (
          <>
            <Card className="border-2 border-primary">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">{hostelInfo.name}</CardTitle>
                    <CardDescription className="text-base">
                      Room {hostelInfo.roomNo} • {hostelInfo.floor}
                    </CardDescription>
                  </div>
                  <Badge className="text-sm">Resident</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Home className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">Building</p>
                      <p className="font-medium">{hostelInfo.building}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">Room Type</p>
                      <p className="font-medium">{hostelInfo.roomType}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Warden Information</CardTitle>
                  <CardDescription>Contact person for hostel matters</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 mb-4">
                    <Avatar className="h-16 w-16">
                      <AvatarFallback className="text-xl">DJ</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{hostelInfo.warden.name}</h3>
                      <p className="text-sm text-muted-foreground">Hostel Warden</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <span>{hostelInfo.warden.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <span>{hostelInfo.warden.email}</span>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-4">
                    <Phone className="h-4 w-4 mr-2" />
                    Contact Warden
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Roommates</CardTitle>
                  <CardDescription>Students sharing the room</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {hostelInfo.roommates.map((roommate, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                        <Avatar>
                          <AvatarFallback>
                            {roommate.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{roommate.name}</p>
                          <p className="text-sm text-muted-foreground">Class {roommate.class}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Hostel Facilities</CardTitle>
                <CardDescription>Available amenities and services</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {hostelInfo.facilities.map((facility, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
                      <span className="text-green-500">✓</span>
                      <span className="text-sm">{facility}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <Home className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">Day Scholar</h3>
              <p className="text-muted-foreground">
                {selectedChildData?.name} is not a hostel resident.
              </p>
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
};

export default ParentHostelInfoPage;
