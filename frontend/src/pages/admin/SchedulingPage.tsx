import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Calendar, Clock, Plus, MoreHorizontal, Edit, Trash2, Download,
  Search, Filter, ChevronLeft, ChevronRight, User, BookOpen, MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

// Types
interface Period {
  id: string;
  day: number;
  period: number;
  subject: string;
  teacher: string;
  room: string;
  startTime: string;
  endTime: string;
  type: "regular" | "lab" | "activity" | "break";
}

// Demo Data
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const PERIODS = [
  { num: 1, start: "08:00", end: "08:45" },
  { num: 2, start: "08:45", end: "09:30" },
  { num: 3, start: "09:30", end: "10:15" },
  { num: 0, start: "10:15", end: "10:30", isBreak: true, label: "Short Break" },
  { num: 4, start: "10:30", end: "11:15" },
  { num: 5, start: "11:15", end: "12:00" },
  { num: 6, start: "12:00", end: "12:45" },
  { num: 0, start: "12:45", end: "13:30", isBreak: true, label: "Lunch Break" },
  { num: 7, start: "13:30", end: "14:15" },
  { num: 8, start: "14:15", end: "15:00" },
];

const DEMO_SCHEDULE: Period[] = [
  // Monday
  { id: "1", day: 0, period: 1, subject: "Mathematics", teacher: "Mr. Sharma", room: "101", startTime: "08:00", endTime: "08:45", type: "regular" },
  { id: "2", day: 0, period: 2, subject: "Mathematics", teacher: "Mr. Sharma", room: "101", startTime: "08:45", endTime: "09:30", type: "regular" },
  { id: "3", day: 0, period: 3, subject: "English", teacher: "Mrs. Verma", room: "101", startTime: "09:30", endTime: "10:15", type: "regular" },
  { id: "4", day: 0, period: 4, subject: "Science", teacher: "Mr. Patel", room: "Lab 1", startTime: "10:30", endTime: "11:15", type: "lab" },
  { id: "5", day: 0, period: 5, subject: "Science", teacher: "Mr. Patel", room: "Lab 1", startTime: "11:15", endTime: "12:00", type: "lab" },
  { id: "6", day: 0, period: 6, subject: "Hindi", teacher: "Mrs. Singh", room: "101", startTime: "12:00", endTime: "12:45", type: "regular" },
  { id: "7", day: 0, period: 7, subject: "Social Science", teacher: "Mr. Gupta", room: "101", startTime: "13:30", endTime: "14:15", type: "regular" },
  { id: "8", day: 0, period: 8, subject: "Computer", teacher: "Mr. Kumar", room: "Computer Lab", startTime: "14:15", endTime: "15:00", type: "lab" },
  // Tuesday
  { id: "9", day: 1, period: 1, subject: "English", teacher: "Mrs. Verma", room: "101", startTime: "08:00", endTime: "08:45", type: "regular" },
  { id: "10", day: 1, period: 2, subject: "Hindi", teacher: "Mrs. Singh", room: "101", startTime: "08:45", endTime: "09:30", type: "regular" },
  { id: "11", day: 1, period: 3, subject: "Mathematics", teacher: "Mr. Sharma", room: "101", startTime: "09:30", endTime: "10:15", type: "regular" },
  { id: "12", day: 1, period: 4, subject: "Mathematics", teacher: "Mr. Sharma", room: "101", startTime: "10:30", endTime: "11:15", type: "regular" },
  { id: "13", day: 1, period: 5, subject: "Science", teacher: "Mr. Patel", room: "101", startTime: "11:15", endTime: "12:00", type: "regular" },
  { id: "14", day: 1, period: 6, subject: "Social Science", teacher: "Mr. Gupta", room: "101", startTime: "12:00", endTime: "12:45", type: "regular" },
  { id: "15", day: 1, period: 7, subject: "Art", teacher: "Mrs. Das", room: "Art Room", startTime: "13:30", endTime: "14:15", type: "activity" },
  { id: "16", day: 1, period: 8, subject: "Sports", teacher: "Mr. Joshi", room: "Ground", startTime: "14:15", endTime: "15:00", type: "activity" },
  // Wednesday
  { id: "17", day: 2, period: 1, subject: "Science", teacher: "Mr. Patel", room: "101", startTime: "08:00", endTime: "08:45", type: "regular" },
  { id: "18", day: 2, period: 2, subject: "Science", teacher: "Mr. Patel", room: "Lab 1", startTime: "08:45", endTime: "09:30", type: "lab" },
  { id: "19", day: 2, period: 3, subject: "Mathematics", teacher: "Mr. Sharma", room: "101", startTime: "09:30", endTime: "10:15", type: "regular" },
  { id: "20", day: 2, period: 4, subject: "English", teacher: "Mrs. Verma", room: "101", startTime: "10:30", endTime: "11:15", type: "regular" },
  { id: "21", day: 2, period: 5, subject: "Hindi", teacher: "Mrs. Singh", room: "101", startTime: "11:15", endTime: "12:00", type: "regular" },
  { id: "22", day: 2, period: 6, subject: "Computer", teacher: "Mr. Kumar", room: "Computer Lab", startTime: "12:00", endTime: "12:45", type: "lab" },
  { id: "23", day: 2, period: 7, subject: "Social Science", teacher: "Mr. Gupta", room: "101", startTime: "13:30", endTime: "14:15", type: "regular" },
  { id: "24", day: 2, period: 8, subject: "Music", teacher: "Mrs. Reddy", room: "Music Room", startTime: "14:15", endTime: "15:00", type: "activity" },
];

const SUBJECT_COLORS: Record<string, string> = {
  "Mathematics": "bg-blue-100 border-blue-300 text-blue-800 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-200",
  "Science": "bg-green-100 border-green-300 text-green-800 dark:bg-green-900/30 dark:border-green-700 dark:text-green-200",
  "English": "bg-purple-100 border-purple-300 text-purple-800 dark:bg-purple-900/30 dark:border-purple-700 dark:text-purple-200",
  "Hindi": "bg-orange-100 border-orange-300 text-orange-800 dark:bg-orange-900/30 dark:border-orange-700 dark:text-orange-200",
  "Social Science": "bg-amber-100 border-amber-300 text-amber-800 dark:bg-amber-900/30 dark:border-amber-700 dark:text-amber-200",
  "Computer": "bg-cyan-100 border-cyan-300 text-cyan-800 dark:bg-cyan-900/30 dark:border-cyan-700 dark:text-cyan-200",
  "Art": "bg-pink-100 border-pink-300 text-pink-800 dark:bg-pink-900/30 dark:border-pink-700 dark:text-pink-200",
  "Music": "bg-rose-100 border-rose-300 text-rose-800 dark:bg-rose-900/30 dark:border-rose-700 dark:text-rose-200",
  "Sports": "bg-emerald-100 border-emerald-300 text-emerald-800 dark:bg-emerald-900/30 dark:border-emerald-700 dark:text-emerald-200",
};

const SchedulingPage = () => {
  const [selectedClass, setSelectedClass] = useState("10-A");
  const [demoMode] = useState(true);

  const getScheduleForSlot = (day: number, period: number) => {
    return DEMO_SCHEDULE.find(s => s.day === day && s.period === period);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">Scheduling</h1>
            {demoMode && (
              <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-800">
                Demo Mode
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground text-sm">Manage class timetables and schedules</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedClass} onValueChange={setSelectedClass}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10-A">Class 10-A</SelectItem>
              <SelectItem value="10-B">Class 10-B</SelectItem>
              <SelectItem value="9-A">Class 9-A</SelectItem>
              <SelectItem value="9-B">Class 9-B</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" /> Export
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" /> Add Period
          </Button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(SUBJECT_COLORS).slice(0, 6).map(([subject, color]) => (
          <Badge key={subject} variant="outline" className={cn("text-xs", color)}>
            {subject}
          </Badge>
        ))}
      </div>

      {/* Timetable Grid */}
      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <div className="min-w-[900px]">
              {/* Header Row */}
              <div className="grid grid-cols-7 bg-muted/50 border-b">
                <div className="p-3 font-medium text-sm text-center border-r">Time</div>
                {DAYS.map((day, i) => (
                  <div key={day} className={cn("p-3 font-medium text-sm text-center", i < 5 && "border-r")}>
                    {day}
                  </div>
                ))}
              </div>

              {/* Period Rows */}
              {PERIODS.map((period, periodIdx) => (
                <div key={periodIdx} className={cn("grid grid-cols-7 border-b last:border-b-0", period.isBreak && "bg-muted/30")}>
                  {/* Time Column */}
                  <div className="p-2 text-sm text-center border-r flex flex-col justify-center">
                    {period.isBreak ? (
                      <span className="text-muted-foreground font-medium">{period.label}</span>
                    ) : (
                      <>
                        <span className="font-medium">Period {period.num}</span>
                        <span className="text-xs text-muted-foreground">{period.start} - {period.end}</span>
                      </>
                    )}
                  </div>

                  {/* Day Columns */}
                  {DAYS.map((_, dayIdx) => {
                    if (period.isBreak) {
                      return (
                        <div key={dayIdx} className={cn("p-2 min-h-[60px] bg-muted/20", dayIdx < 5 && "border-r")} />
                      );
                    }

                    const slot = getScheduleForSlot(dayIdx, period.num);
                    return (
                      <div key={dayIdx} className={cn("p-1 min-h-[70px]", dayIdx < 5 && "border-r")}>
                        {slot ? (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className={cn(
                              "h-full rounded-md border p-2 cursor-pointer hover:shadow-md transition-shadow",
                              SUBJECT_COLORS[slot.subject] || "bg-gray-100 border-gray-300"
                            )}
                          >
                            <p className="font-medium text-xs truncate">{slot.subject}</p>
                            <div className="flex items-center gap-1 mt-1 text-[10px] opacity-80">
                              <User className="h-2.5 w-2.5" />
                              <span className="truncate">{slot.teacher}</span>
                            </div>
                            <div className="flex items-center gap-1 text-[10px] opacity-80">
                              <MapPin className="h-2.5 w-2.5" />
                              <span>{slot.room}</span>
                            </div>
                          </motion.div>
                        ) : (
                          <div className="h-full rounded-md border border-dashed border-muted-foreground/20 flex items-center justify-center">
                            <Plus className="h-4 w-4 text-muted-foreground/30" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Periods", value: 48, icon: Clock },
          { label: "Subjects", value: 9, icon: BookOpen },
          { label: "Teachers Assigned", value: 8, icon: User },
          { label: "Lab Sessions", value: 6, icon: Calendar },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <stat.icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-lg font-bold">{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default SchedulingPage;
