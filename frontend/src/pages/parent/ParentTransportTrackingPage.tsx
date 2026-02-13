import { useState } from "react";
import { motion } from "framer-motion";
import { Bus, MapPin, Clock, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const ParentTransportTrackingPage = () => {
  const [selectedChild, setSelectedChild] = useState("1");

  const children = [
    { id: "1", name: "John Doe", class: "10-A", busNo: "BUS-05", route: "Route A" },
    { id: "2", name: "Jane Doe", class: "8-B", busNo: "BUS-12", route: "Route B" },
  ];

  const selectedChildData = children.find(c => c.id === selectedChild);

  const busInfo = {
    number: "BUS-05",
    route: "Route A",
    driver: "Mr. Robert Smith",
    driverPhone: "+1 234-567-8900",
    currentLocation: "Near Central Park",
    eta: "15 minutes",
    status: "On Time",
    stops: [
      { name: "School", time: "07:00 AM", status: "Departed" },
      { name: "Main Street", time: "07:15 AM", status: "Completed" },
      { name: "Central Park", time: "07:30 AM", status: "Current" },
      { name: "Your Stop", time: "07:45 AM", status: "Upcoming" },
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
              <Bus className="h-8 w-8 text-primary" />
              Transport Tracking
            </h1>
            <p className="text-muted-foreground mt-1">Track your child&apos;s school bus in real-time</p>
          </div>
          <Select value={selectedChild} onValueChange={setSelectedChild}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select child" />
            </SelectTrigger>
            <SelectContent>
              {children.map((child) => (
                <SelectItem key={child.id} value={child.id}>
                  {child.name} - {child.busNo}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedChildData && (
          <>
            <Card className="border-2 border-primary">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">{busInfo.number}</CardTitle>
                    <CardDescription className="text-base">{busInfo.route}</CardDescription>
                  </div>
                  <Badge className="text-sm" variant={busInfo.status === "On Time" ? "default" : "destructive"}>
                    {busInfo.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">Current Location</p>
                      <p className="font-medium">{busInfo.currentLocation}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm text-muted-foreground">ETA to Your Stop</p>
                      <p className="font-medium">{busInfo.eta}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Driver Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <Avatar className="h-16 w-16">
                      <AvatarFallback className="text-xl">RS</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{busInfo.driver}</h3>
                      <div className="flex items-center gap-2 mt-2">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{busInfo.driverPhone}</span>
                      </div>
                    </div>
                    <Button variant="outline">
                      <Phone className="h-4 w-4 mr-2" />
                      Call
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Route Stops</CardTitle>
                  <CardDescription>Bus route and schedule</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {busInfo.stops.map((stop, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                          stop.status === "Completed" ? "bg-green-500" :
                          stop.status === "Current" ? "bg-blue-500" :
                          "bg-gray-300"
                        }`}>
                          {stop.status === "Completed" && <span className="text-white text-xs">✓</span>}
                          {stop.status === "Current" && <span className="text-white text-xs">●</span>}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{stop.name}</p>
                          <p className="text-sm text-muted-foreground">{stop.time}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {stop.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Live Map</CardTitle>
                <CardDescription>Real-time bus location</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                  <p className="text-muted-foreground">Map integration coming soon...</p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default ParentTransportTrackingPage;
