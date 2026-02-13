import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import {
  Bell, Check, CheckCheck, Trash2, Settings, Filter, Search,
  MessageSquare, DollarSign, Calendar, FileText, AlertCircle,
  Award, Users, BookOpen, Clock, ChevronRight, MoreHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

// Types
type NotificationType = "message" | "payment" | "attendance" | "grade" | "event" | "announcement" | "alert";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  description: string;
  time: Date;
  read: boolean;
  actionUrl?: string;
}

// Demo data
const DEMO_NOTIFICATIONS: Notification[] = [
  { id: "1", type: "message", title: "New message from Mrs. Sharma", description: "Regarding Aisha's performance in Mathematics", time: new Date(Date.now() - 1000 * 60 * 30), read: false },
  { id: "2", type: "payment", title: "Fee payment reminder", description: "₹15,000 pending for December. Due in 7 days.", time: new Date(Date.now() - 1000 * 60 * 60 * 2), read: false },
  { id: "3", type: "attendance", title: "Attendance marked", description: "Aisha was marked present today", time: new Date(Date.now() - 1000 * 60 * 60 * 4), read: true },
  { id: "4", type: "grade", title: "Assignment graded", description: "Mathematics assignment scored 92/100", time: new Date(Date.now() - 1000 * 60 * 60 * 24), read: true },
  { id: "5", type: "event", title: "Parent-Teacher Meeting", description: "Scheduled for December 20, 2024 at 10:00 AM", time: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), read: true },
  { id: "6", type: "announcement", title: "Winter vacation dates", description: "School will remain closed from Dec 25 to Jan 1", time: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), read: true },
  { id: "7", type: "alert", title: "System maintenance", description: "Scheduled downtime on Sunday 2-4 AM", time: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5), read: true },
];

const TYPE_CONFIG: Record<NotificationType, { icon: React.ElementType; color: string; bgColor: string }> = {
  message: { icon: MessageSquare, color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-900/30" },
  payment: { icon: DollarSign, color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-900/30" },
  attendance: { icon: CheckCheck, color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-900/30" },
  grade: { icon: Award, color: "text-purple-600", bgColor: "bg-purple-100 dark:bg-purple-900/30" },
  event: { icon: Calendar, color: "text-cyan-600", bgColor: "bg-cyan-100 dark:bg-cyan-900/30" },
  announcement: { icon: Bell, color: "text-rose-600", bgColor: "bg-rose-100 dark:bg-rose-900/30" },
  alert: { icon: AlertCircle, color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-900/30" },
};

const NotificationsPage = () => {
  const [notifications, setNotifications] = useState(DEMO_NOTIFICATIONS);
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");

  const unreadCount = useMemo(() => notifications.filter(n => !n.read).length, [notifications]);

  const filteredNotifications = useMemo(() => {
    return notifications.filter(n => {
      const matchesSearch = n.title.toLowerCase().includes(search.toLowerCase()) ||
        n.description.toLowerCase().includes(search.toLowerCase());
      const matchesTab = tab === "all" || (tab === "unread" && !n.read);
      return matchesSearch && matchesTab;
    });
  }, [notifications, search, tab]);

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Notifications</h1>
            {unreadCount > 0 && (
              <Badge className="rounded-full">{unreadCount} new</Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Stay updated with your activities</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={markAllAsRead} disabled={unreadCount === 0}>
            <CheckCheck className="h-4 w-4 mr-1" /> Mark all read
          </Button>
          <Button variant="outline" size="icon" className="h-9 w-9">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="unread">
              Unread {unreadCount > 0 && `(${unreadCount})`}
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search notifications..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Notifications List */}
      <Card>
        <CardContent className="p-0">
          {filteredNotifications.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No notifications found</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredNotifications.map((notification, i) => {
                const config = TYPE_CONFIG[notification.type];
                const Icon = config.icon;
                return (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className={cn(
                      "flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer",
                      !notification.read && "bg-primary/5"
                    )}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center shrink-0", config.bgColor)}>
                      <Icon className={cn("h-5 w-5", config.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className={cn("font-medium text-sm", !notification.read && "font-semibold")}>
                            {notification.title}
                          </p>
                          <p className="text-sm text-muted-foreground mt-0.5">{notification.description}</p>
                        </div>
                        {!notification.read && (
                          <div className="h-2 w-2 rounded-full bg-primary shrink-0 mt-2" />
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDistanceToNow(notification.time, { addSuffix: true })}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {!notification.read && (
                          <DropdownMenuItem onClick={() => markAsRead(notification.id)}>
                            <Check className="h-3.5 w-3.5 mr-2" /> Mark as read
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem className="text-destructive" onClick={() => deleteNotification(notification.id)}>
                          <Trash2 className="h-3.5 w-3.5 mr-2" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </motion.div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationsPage;
