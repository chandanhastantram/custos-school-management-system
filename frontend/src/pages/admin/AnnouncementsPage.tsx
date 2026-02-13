import { useState } from "react";
import { motion } from "framer-motion";
import { Megaphone, Plus, Search, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const AnnouncementsPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const announcements = [
    { 
      id: 1, 
      title: "School Reopening After Winter Break", 
      content: "School will reopen on February 15th. All students are expected to attend...",
      author: "Principal",
      date: "2024-02-10",
      target: "All",
      priority: "High",
      views: 450
    },
    { 
      id: 2, 
      title: "Sports Day Registration Open", 
      content: "Registration for annual sports day is now open. Students can register...",
      author: "Sports Coordinator",
      date: "2024-02-12",
      target: "Students",
      priority: "Medium",
      views: 320
    },
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
              <Megaphone className="h-8 w-8 text-primary" />
              Announcements
            </h1>
            <p className="text-muted-foreground mt-1">Broadcast important messages to stakeholders</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Announcement
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Announcements</CardDescription>
              <CardTitle className="text-3xl">24</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Month</CardDescription>
              <CardTitle className="text-3xl">8</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Views</CardDescription>
              <CardTitle className="text-3xl">12.5K</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg. Reach</CardDescription>
              <CardTitle className="text-3xl">85%</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="students">Students</TabsTrigger>
            <TabsTrigger value="parents">Parents</TabsTrigger>
            <TabsTrigger value="staff">Staff</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>All Announcements</CardTitle>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search announcements..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {announcements.map((announcement) => (
                    <Card key={announcement.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-lg">{announcement.title}</CardTitle>
                              <Badge variant={announcement.priority === "High" ? "destructive" : "default"}>
                                {announcement.priority}
                              </Badge>
                            </div>
                            <CardDescription>{announcement.content}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <Avatar className="h-8 w-8">
                                <AvatarFallback>{announcement.author[0]}</AvatarFallback>
                              </Avatar>
                              <div className="text-sm">
                                <p className="font-medium">{announcement.author}</p>
                                <p className="text-muted-foreground">{announcement.date}</p>
                              </div>
                            </div>
                            <Badge variant="outline">{announcement.target}</Badge>
                            <span className="text-sm text-muted-foreground">👁️ {announcement.views} views</span>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">Edit</Button>
                            <Button size="sm">
                              <Send className="h-4 w-4 mr-2" />
                              Resend
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="students">
            <Card>
              <CardHeader>
                <CardTitle>Student Announcements</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="parents">
            <Card>
              <CardHeader>
                <CardTitle>Parent Announcements</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="staff">
            <Card>
              <CardHeader>
                <CardTitle>Staff Announcements</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Filtered view coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default AnnouncementsPage;
