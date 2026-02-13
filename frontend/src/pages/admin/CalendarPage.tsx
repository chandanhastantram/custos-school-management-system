import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar as CalendarIcon, Plus, Filter, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

const CalendarPage = () => {
  const upcomingEvents = [
    { id: 1, title: "Annual Sports Day", date: "2024-02-20", time: "09:00 AM", type: "Event", attendees: 500, location: "Main Ground" },
    { id: 2, title: "Parent-Teacher Meeting", date: "2024-02-25", time: "02:00 PM", type: "Meeting", attendees: 150, location: "Auditorium" },
    { id: 3, title: "Science Exhibition", date: "2024-03-05", time: "10:00 AM", type: "Event", attendees: 300, location: "Science Block" },
  ];

  const holidays = [
    { id: 1, name: "Republic Day", date: "2024-01-26", type: "National" },
    { id: 2, name: "Holi", date: "2024-03-25", type: "Festival" },
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
              <CalendarIcon className="h-8 w-8 text-primary" />
              Academic Calendar
            </h1>
            <p className="text-muted-foreground mt-1">Manage events, holidays, and important dates</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Event
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Upcoming Events</CardDescription>
              <CardTitle className="text-3xl">12</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Month</CardDescription>
              <CardTitle className="text-3xl">5</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Holidays</CardDescription>
              <CardTitle className="text-3xl">8</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Working Days</CardDescription>
              <CardTitle className="text-3xl">220</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="events" className="space-y-4">
          <TabsList>
            <TabsTrigger value="events">Events</TabsTrigger>
            <TabsTrigger value="holidays">Holidays</TabsTrigger>
            <TabsTrigger value="calendar">Calendar View</TabsTrigger>
          </TabsList>

          <TabsContent value="events">
            <Card>
              <CardHeader>
                <CardTitle>Upcoming Events</CardTitle>
                <CardDescription>School events and activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {upcomingEvents.map((event) => (
                    <Card key={event.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg">{event.title}</CardTitle>
                            <CardDescription className="flex items-center gap-4 mt-2">
                              <span className="flex items-center gap-1">
                                <CalendarIcon className="h-4 w-4" />
                                {event.date}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                {event.time}
                              </span>
                            </CardDescription>
                          </div>
                          <Badge>{event.type}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="text-sm text-muted-foreground">
                            <p>📍 {event.location}</p>
                            <p>👥 {event.attendees} attendees</p>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">Edit</Button>
                            <Button size="sm">View Details</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="holidays">
            <Card>
              <CardHeader>
                <CardTitle>Holiday Calendar</CardTitle>
                <CardDescription>Academic year holidays and breaks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {holidays.map((holiday) => (
                    <div key={holiday.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-semibold">{holiday.name}</h4>
                        <p className="text-sm text-muted-foreground">{holiday.date}</p>
                      </div>
                      <Badge variant="outline">{holiday.type}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="calendar">
            <Card>
              <CardHeader>
                <CardTitle>Calendar View</CardTitle>
                <CardDescription>Visual calendar with all events</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Interactive calendar view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default CalendarPage;
