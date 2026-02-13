import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  Bus, MapPin, Navigation, Clock, 
  Users, AlertTriangle, ShieldCheck, 
  Search, Filter, Plus, Phone,
  ChevronRight, ArrowRight, Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

const DEMO_ROUTES = [
  { id: "1", name: "Route A - North", vehicle: "Bus 12 (MH-01-1234)", driver: "Suresh Kumar", students: 42, stops: 8, status: "on-time" },
  { id: "2", name: "Route B - South", vehicle: "Bus 08 (MH-01-5678)", driver: "Ramesh Singh", students: 35, stops: 6, status: "delayed" },
  { id: "3", name: "Route C - East", vehicle: "Bus 15 (MH-01-9012)", driver: "Amit Patel", students: 30, stops: 10, status: "completed" },
];

const TransportPage = () => {
  const [activeView, setActiveView] = useState("routes");

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Transport Management</h1>
          <p className="text-muted-foreground text-sm">Monitor school vehicles, routes, and student assignments</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" /> Settings
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" /> New Route
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <Tabs defaultValue="routes" className="w-full">
            <div className="px-6 pt-6 flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="routes">Active Routes</TabsTrigger>
                <TabsTrigger value="vehicles">Vehicles</TabsTrigger>
                <TabsTrigger value="drivers">Drivers</TabsTrigger>
              </TabsList>
              <div className="relative w-48 hidden sm:block">
                <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                <Input placeholder="Search..." className="pl-8 h-8 text-xs" />
              </div>
            </div>

            <TabsContent value="routes" className="p-6 pt-4">
              <div className="space-y-4">
                {DEMO_ROUTES.map((route, i) => (
                  <motion.div
                    key={route.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="group border rounded-xl overflow-hidden hover:border-primary/50 transition-colors"
                  >
                    <div className="p-4 bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-4">
                        <div className={cn(
                          "h-12 w-12 rounded-lg flex items-center justify-center",
                          route.status === "on-time" ? "bg-emerald-50 text-emerald-600" : 
                          route.status === "delayed" ? "bg-amber-50 text-amber-600" : "bg-blue-50 text-blue-600"
                        )}>
                          <Bus className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">{route.name}</h3>
                          <p className="text-sm text-muted-foreground flex items-center gap-1">
                            <Users className="h-3 w-3" /> {route.students} Students · <MapPin className="h-3 w-3" /> {route.stops} Stops
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right hidden sm:block">
                          <p className="text-xs font-semibold">{route.driver}</p>
                          <p className="text-[10px] text-muted-foreground">{route.vehicle}</p>
                        </div>
                        <Badge variant="outline" className={cn(
                          "uppercase text-[10px]",
                          route.status === "on-time" ? "border-emerald-200 text-emerald-600 font-bold" : 
                          route.status === "delayed" ? "border-amber-200 text-amber-600 font-bold" : "border-blue-200 text-blue-600 font-bold"
                        )}>
                          {route.status}
                        </Badge>
                        <Button variant="ghost" size="icon" className="group-hover:translate-x-1 transition-transform">
                          <ChevronRight className="h-5 w-5" />
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </Card>

        <div className="space-y-6">
          <Card className="bg-primary/5 border-primary/20 overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Navigation className="h-24 w-24 rotate-12" />
            </div>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 text-primary">
                <ShieldCheck className="h-5 w-5" /> Safety Status
              </CardTitle>
              <CardDescription>Live fleet health monitoring</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Buses Active</span>
                <span className="text-xl font-bold">12/15</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Verified Drivers</span>
                <span className="text-xl font-bold text-emerald-600">100%</span>
              </div>
              <div className="pt-4 border-t border-primary/10">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-background/50 border border-amber-200/50">
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-bold text-amber-700">Delayed Alert</p>
                    <p className="text-[10px] text-amber-600">Route B is 15 mins behind due to traffic at MG Road.</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Contact</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start text-xs h-10">
                <Phone className="h-3 w-3 mr-2 text-emerald-600" /> Transport In-charge
              </Button>
              <Button variant="outline" className="w-full justify-start text-xs h-10">
                <Phone className="h-3 w-3 mr-2 text-blue-600" /> Emergency Support
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TransportPage;
