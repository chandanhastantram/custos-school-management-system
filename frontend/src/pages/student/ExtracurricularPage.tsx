import { useState } from "react";
import { motion } from "framer-motion";
import { Trophy, Calendar, Users, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

const ExtracurricularPage = () => {
  const myActivities = [
    { id: 1, name: "Chess Club", role: "Member", schedule: "Wednesdays 4-5 PM", points: 50 },
    { id: 2, name: "Science Club", role: "President", schedule: "Fridays 3-5 PM", points: 100 },
  ];

  const availableActivities = [
    { id: 3, name: "Drama Club", category: "Arts", schedule: "Tuesdays 4-6 PM", members: 25, openSlots: 5 },
    { id: 4, name: "Basketball Team", category: "Sports", schedule: "Mon, Thu 5-6 PM", members: 15, openSlots: 3 },
  ];

  const achievements = [
    { id: 1, title: "Science Fair Winner", date: "2024-02-10", points: 100, badge: "🏆" },
    { id: 2, title: "Chess Tournament - 2nd Place", date: "2024-01-25", points: 75, badge: "🥈" },
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
              <Trophy className="h-8 w-8 text-primary" />
              Extracurricular Activities
            </h1>
            <p className="text-muted-foreground mt-1">Join clubs, sports, and earn activity points</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>My Activities</CardDescription>
              <CardTitle className="text-3xl">2</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Points</CardDescription>
              <CardTitle className="text-3xl">225</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Achievements</CardDescription>
              <CardTitle className="text-3xl">8</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Class Rank</CardDescription>
              <CardTitle className="text-3xl">#3</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Tabs defaultValue="my-activities" className="space-y-4">
          <TabsList>
            <TabsTrigger value="my-activities">My Activities</TabsTrigger>
            <TabsTrigger value="available">Available</TabsTrigger>
            <TabsTrigger value="achievements">Achievements</TabsTrigger>
          </TabsList>

          <TabsContent value="my-activities">
            <Card>
              <CardHeader>
                <CardTitle>My Enrolled Activities</CardTitle>
                <CardDescription>Activities you're currently participating in</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {myActivities.map((activity) => (
                    <Card key={activity.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{activity.name}</CardTitle>
                            <CardDescription className="flex items-center gap-4 mt-2">
                              <span className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {activity.schedule}
                              </span>
                            </CardDescription>
                          </div>
                          <Badge>{activity.role}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="text-sm">
                            <p className="text-muted-foreground">Points Earned</p>
                            <p className="text-2xl font-bold text-primary">{activity.points}</p>
                          </div>
                          <Button variant="outline" size="sm">View Details</Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="available">
            <Card>
              <CardHeader>
                <CardTitle>Available Activities</CardTitle>
                <CardDescription>Join new clubs and activities</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {availableActivities.map((activity) => (
                    <Card key={activity.id} className="border-2">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">{activity.name}</CardTitle>
                            <CardDescription className="flex items-center gap-4 mt-2">
                              <Badge variant="outline">{activity.category}</Badge>
                              <span className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {activity.schedule}
                              </span>
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm">
                            <span className="flex items-center gap-1">
                              <Users className="h-4 w-4" />
                              {activity.members} members
                            </span>
                            <span className="text-green-600">{activity.openSlots} slots open</span>
                          </div>
                          <Button size="sm">
                            <Plus className="h-4 w-4 mr-2" />
                            Join
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements">
            <Card>
              <CardHeader>
                <CardTitle>My Achievements</CardTitle>
                <CardDescription>Badges and awards earned</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {achievements.map((achievement) => (
                    <div key={achievement.id} className="flex items-center gap-4 p-4 border rounded-lg">
                      <div className="text-4xl">{achievement.badge}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold">{achievement.title}</h4>
                        <p className="text-sm text-muted-foreground">{achievement.date}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Points</p>
                        <p className="text-xl font-bold text-primary">+{achievement.points}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ExtracurricularPage;
