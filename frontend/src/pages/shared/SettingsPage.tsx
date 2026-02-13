import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Settings, User, Bell, Lock, Palette, Globe, Shield,
  Moon, Sun, Monitor, ChevronRight, LogOut, Camera,
  Mail, Phone, Building, Calendar, Eye, EyeOff, Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Types
interface SettingSection {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
}

const SECTIONS: SettingSection[] = [
  { id: "profile", title: "Profile", description: "Manage your personal information", icon: User },
  { id: "notifications", title: "Notifications", description: "Configure notification preferences", icon: Bell },
  { id: "appearance", title: "Appearance", description: "Customize the look and feel", icon: Palette },
  { id: "security", title: "Security", description: "Password and authentication", icon: Lock },
];

const SettingsPage = () => {
  const { theme, setTheme } = useTheme();
  const [activeSection, setActiveSection] = useState("profile");
  const [showPassword, setShowPassword] = useState(false);

  // Demo profile data
  const [profile, setProfile] = useState({
    firstName: "Admin",
    lastName: "User",
    email: "admin@custos.school",
    phone: "+91 98765 43210",
    role: "Super Admin",
    school: "CUSTOS International School",
    joinDate: "2023-04-01",
  });

  // Notification settings
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    sms: false,
    attendance: true,
    grades: true,
    payments: true,
    announcements: true,
    messages: true,
  });

  const handleSave = () => {
    toast({
      title: "Settings saved",
      description: "Your preferences have been updated successfully.",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm">Manage your account and preferences</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar */}
        <Card className="lg:col-span-1 h-fit">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                    activeSection === section.id
                      ? "bg-primary/10 text-primary"
                      : "hover:bg-muted"
                  )}
                >
                  <section.icon className="h-4 w-4" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{section.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{section.description}</p>
                  </div>
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        {/* Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Profile Section */}
          {activeSection === "profile" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Profile Information</CardTitle>
                  <CardDescription>Update your personal details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Avatar */}
                  <div className="flex items-center gap-4">
                    <Avatar className="h-20 w-20">
                      <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
                        {profile.firstName[0]}{profile.lastName[0]}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <Button variant="outline" size="sm">
                        <Camera className="h-4 w-4 mr-1" /> Change Photo
                      </Button>
                      <p className="text-xs text-muted-foreground mt-1">JPG, PNG or GIF. Max 2MB</p>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input id="firstName" value={profile.firstName} onChange={(e) => setProfile({ ...profile, firstName: e.target.value })} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input id="lastName" value={profile.lastName} onChange={(e) => setProfile({ ...profile, lastName: e.target.value })} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input id="email" type="email" value={profile.email} className="pl-9" readOnly />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input id="phone" value={profile.phone} className="pl-9" onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{profile.role}</span>
                        <Badge variant="secondary" className="text-xs">Admin</Badge>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>School</Label>
                      <div className="flex items-center gap-2">
                        <Building className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{profile.school}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Notifications Section */}
          {activeSection === "notifications" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Notification Channels</CardTitle>
                  <CardDescription>Choose how you want to receive notifications</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { key: "email", label: "Email Notifications", description: "Receive updates via email" },
                    { key: "push", label: "Push Notifications", description: "Browser and mobile notifications" },
                    { key: "sms", label: "SMS Notifications", description: "Text message alerts" },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{item.label}</p>
                        <p className="text-xs text-muted-foreground">{item.description}</p>
                      </div>
                      <Switch
                        checked={notifications[item.key as keyof typeof notifications]}
                        onCheckedChange={(checked) => setNotifications({ ...notifications, [item.key]: checked })}
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Notification Types</CardTitle>
                  <CardDescription>Select which notifications you want to receive</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { key: "attendance", label: "Attendance Updates" },
                    { key: "grades", label: "Grade & Results" },
                    { key: "payments", label: "Payment Reminders" },
                    { key: "announcements", label: "School Announcements" },
                    { key: "messages", label: "New Messages" },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between">
                      <p className="text-sm">{item.label}</p>
                      <Switch
                        checked={notifications[item.key as keyof typeof notifications]}
                        onCheckedChange={(checked) => setNotifications({ ...notifications, [item.key]: checked })}
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Appearance Section */}
          {activeSection === "appearance" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Theme</CardTitle>
                  <CardDescription>Select your preferred color theme</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { value: "light", label: "Light", icon: Sun },
                      { value: "dark", label: "Dark", icon: Moon },
                      { value: "system", label: "System", icon: Monitor },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setTheme(option.value as "light" | "dark" | "system")}
                        className={cn(
                          "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors",
                          theme === option.value
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-muted-foreground/50"
                        )}
                      >
                        <option.icon className={cn("h-6 w-6", theme === option.value && "text-primary")} />
                        <span className="text-sm font-medium">{option.label}</span>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Language</CardTitle>
                  <CardDescription>Choose your preferred language</CardDescription>
                </CardHeader>
                <CardContent>
                  <Select defaultValue="en">
                    <SelectTrigger className="w-full sm:w-[200px]">
                      <Globe className="h-4 w-4 mr-2" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="hi">हिंदी (Hindi)</SelectItem>
                      <SelectItem value="ta">தமிழ் (Tamil)</SelectItem>
                      <SelectItem value="te">తెలుగు (Telugu)</SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Security Section */}
          {activeSection === "security" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Change Password</CardTitle>
                  <CardDescription>Update your password regularly to keep your account secure</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <div className="relative">
                      <Input id="currentPassword" type={showPassword ? "text" : "password"} />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input id="newPassword" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input id="confirmPassword" type="password" />
                  </div>
                  <Button>Update Password</Button>
                </CardContent>
              </Card>

              <Card className="border-destructive/50">
                <CardHeader>
                  <CardTitle className="text-base text-destructive">Danger Zone</CardTitle>
                  <CardDescription>Irreversible actions</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="destructive">
                    <LogOut className="h-4 w-4 mr-1" /> Sign Out from All Devices
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Save Button */}
          <div className="flex justify-end">
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-1" /> Save Changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
