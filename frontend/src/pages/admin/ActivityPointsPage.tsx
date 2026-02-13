import { useState } from "react";
import { motion } from "framer-motion";
import { Trophy, Plus, Search, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const ActivityPointsPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data
  const activities = [
    { id: 1, name: "Sports Day Participation", category: "Sports", points: 50, status: "Active" },
    { id: 2, name: "Science Fair Winner", category: "Academic", points: 100, status: "Active" },
    { id: 3, name: "Community Service", category: "Social", points: 75, status: "Active" },
  ];

  const leaderboard = [
    { rank: 1, name: "Alex Chen", class: "10-A", points: 450, badges: 12 },
    { rank: 2, name: "Sarah Johnson", class: "10-B", points: 420, badges: 10 },
    { rank: 3, name: "Michael Brown", class: "9-A", points: 380, badges: 9 },
  ];

  const recentAwards = [
    { id: 1, student: "John Doe", activity: "Sports Day Participation", points: 50, date: "2024-02-13" },
    { id: 2, student: "Jane Smith", activity: "Science Fair Winner", points: 100, date: "2024-02-12" },
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
              <Trophy className="h-8 w-8 text-primary" />
              Activity Points
            </h1>
            <p className="text-muted-foreground mt-1">Manage extracurricular activities and student achievements</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              New Activity
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Award Points
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Activities</CardDescription>
              <CardTitle className="text-3xl">24</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Points Awarded</CardDescription>
              <CardTitle className="text-3xl">12,450</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Students</CardDescription>
              <CardTitle className="text-3xl">320</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>This Month</CardDescription>
              <CardTitle className="text-3xl flex items-center gap-1">
                <TrendingUp className="h-5 w-5 text-green-500" />
                +15%
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="activities" className="space-y-4">
          <TabsList>
            <TabsTrigger value="activities">Activities</TabsTrigger>
            <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
            <TabsTrigger value="awards">Recent Awards</TabsTrigger>
            <TabsTrigger value="categories">Categories</TabsTrigger>
          </TabsList>

          <TabsContent value="activities" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Activity Catalog</CardTitle>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search activities..."
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
                      <TableHead>Activity Name</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Points</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {activities.map((activity) => (
                      <TableRow key={activity.id}>
                        <TableCell className="font-medium">{activity.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{activity.category}</Badge>
                        </TableCell>
                        <TableCell className="font-semibold text-primary">{activity.points} pts</TableCell>
                        <TableCell>
                          <Badge variant="default">{activity.status}</Badge>
                        </TableCell>
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

          <TabsContent value="leaderboard" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Top Performers</CardTitle>
                <CardDescription>Students ranked by total activity points</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {leaderboard.map((student) => (
                    <div key={student.rank} className="flex items-center gap-4 p-4 border rounded-lg">
                      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary font-bold text-xl">
                        #{student.rank}
                      </div>
                      <Avatar className="h-12 w-12">
                        <AvatarFallback>{student.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <h4 className="font-semibold">{student.name}</h4>
                        <p className="text-sm text-muted-foreground">Class {student.class}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-primary">{student.points}</p>
                        <p className="text-sm text-muted-foreground">{student.badges} badges</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="awards" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Awards</CardTitle>
                <CardDescription>Latest activity points awarded to students</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Student</TableHead>
                      <TableHead>Activity</TableHead>
                      <TableHead>Points</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentAwards.map((award) => (
                      <TableRow key={award.id}>
                        <TableCell className="font-medium">{award.student}</TableCell>
                        <TableCell>{award.activity}</TableCell>
                        <TableCell className="font-semibold text-primary">+{award.points}</TableCell>
                        <TableCell>{award.date}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="categories" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Activity Categories</CardTitle>
                <CardDescription>Manage activity categories and point ranges</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Category management interface coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ActivityPointsPage;
