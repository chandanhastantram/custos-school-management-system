import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Calendar, Sparkles, Wand2, Clock, Users, BookOpen, AlertTriangle,
  Check, RefreshCw, Download, Settings, ChevronRight, Loader2,
  Zap, Crown, Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { FeatureGate, MaxBadge } from "@/components/FeatureGate";
import { useAIQueryLimit } from "@/hooks/useFeatureGate";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Types
interface ScheduleConstraint {
  id: string;
  type: "teacher" | "room" | "subject" | "break";
  description: string;
  enabled: boolean;
}

interface GeneratedSlot {
  day: string;
  period: number;
  subject: string;
  teacher: string;
  room: string;
  hasConflict?: boolean;
}

interface GenerationResult {
  success: boolean;
  slots: GeneratedSlot[];
  conflicts: number;
  optimizationScore: number;
  suggestions: string[];
}

// Demo constraints
const DEMO_CONSTRAINTS: ScheduleConstraint[] = [
  { id: "1", type: "teacher", description: "Teachers max 6 periods/day", enabled: true },
  { id: "2", type: "room", description: "Lab sessions in designated rooms only", enabled: true },
  { id: "3", type: "subject", description: "No consecutive same-subject periods", enabled: true },
  { id: "4", type: "break", description: "Include lunch break 12:30-1:30 PM", enabled: true },
  { id: "5", type: "teacher", description: "Morning preference for senior teachers", enabled: false },
  { id: "6", type: "subject", description: "Math/Science in morning slots", enabled: true },
];

// Demo generated schedule
const DEMO_SCHEDULE: GeneratedSlot[] = [
  { day: "Monday", period: 1, subject: "Mathematics", teacher: "Mr. Sharma", room: "101" },
  { day: "Monday", period: 2, subject: "Science", teacher: "Mr. Patel", room: "Lab 1" },
  { day: "Monday", period: 3, subject: "English", teacher: "Mrs. Verma", room: "102" },
  { day: "Monday", period: 4, subject: "Hindi", teacher: "Mrs. Singh", room: "101" },
  { day: "Monday", period: 5, subject: "Social Science", teacher: "Mr. Gupta", room: "103" },
  { day: "Tuesday", period: 1, subject: "Science", teacher: "Mr. Patel", room: "Lab 1" },
  { day: "Tuesday", period: 2, subject: "Mathematics", teacher: "Mr. Sharma", room: "101" },
  { day: "Tuesday", period: 3, subject: "Computer", teacher: "Mr. Kumar", room: "Lab 2" },
  { day: "Tuesday", period: 4, subject: "English", teacher: "Mrs. Verma", room: "102" },
  { day: "Tuesday", period: 5, subject: "Physical Ed", teacher: "Mr. Singh", room: "Ground", hasConflict: true },
];

const AIScheduleMakerContent = () => {
  const [constraints, setConstraints] = useState(DEMO_CONSTRAINTS);
  const [selectedClass, setSelectedClass] = useState<string>("10-A");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const { canQuery, useQuery, usageText } = useAIQueryLimit();

  const toggleConstraint = (id: string) => {
    setConstraints(prev => prev.map(c => 
      c.id === id ? { ...c, enabled: !c.enabled } : c
    ));
  };

  const generateSchedule = async () => {
    if (!canQuery) {
      toast({
        title: "Query limit reached",
        description: "Upgrade your plan for more AI queries",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    setGenerationStep(0);
    setResult(null);
    useQuery();

    // Simulate multi-step generation
    const steps = [
      "Analyzing teacher availability...",
      "Checking room allocations...",
      "Applying subject constraints...",
      "Optimizing for conflicts...",
      "Finalizing schedule...",
    ];

    for (let i = 0; i < steps.length; i++) {
      await new Promise(r => setTimeout(r, 800));
      setGenerationStep(i + 1);
    }

    setResult({
      success: true,
      slots: DEMO_SCHEDULE,
      conflicts: 1,
      optimizationScore: 94,
      suggestions: [
        "Consider moving Physical Ed to morning for better engagement",
        "Mr. Patel has back-to-back lab sessions on Wednesday",
        "Room 102 is underutilized on Fridays",
      ],
    });
    setIsGenerating(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
            <Wand2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">AI Schedule Maker</h1>
              <MaxBadge />
            </div>
            <p className="text-muted-foreground text-sm">Intelligent timetable generation</p>
          </div>
        </div>
        <Badge variant="outline">{usageText}</Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-4">
          {/* Class Selection */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Select Class</Label>
                <Select value={selectedClass} onValueChange={setSelectedClass}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["9-A", "9-B", "10-A", "10-B", "11-A", "11-B", "12-A", "12-B"].map(cls => (
                      <SelectItem key={cls} value={cls}>Class {cls}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Academic Year</Label>
                <Select defaultValue="2024-25">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2024-25">2024-25</SelectItem>
                    <SelectItem value="2025-26">2025-26</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Constraints */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Constraints
              </CardTitle>
              <CardDescription>Configure scheduling rules</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {constraints.map((constraint) => (
                <div key={constraint.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">
                      {constraint.type}
                    </Badge>
                    <span className="text-sm">{constraint.description}</span>
                  </div>
                  <Switch
                    checked={constraint.enabled}
                    onCheckedChange={() => toggleConstraint(constraint.id)}
                  />
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Generate Button */}
          <Button 
            className="w-full gap-2" 
            size="lg"
            onClick={generateSchedule}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate Schedule
              </>
            )}
          </Button>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-4">
          {isGenerating && (
            <Card>
              <CardContent className="py-8">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
                  <h3 className="font-semibold mb-2">Generating Optimal Schedule</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Step {generationStep}/5: {
                      ["Analyzing teacher availability...",
                       "Checking room allocations...",
                       "Applying subject constraints...",
                       "Optimizing for conflicts...",
                       "Finalizing schedule..."][generationStep - 1] || "Initializing..."
                    }
                  </p>
                  <Progress value={generationStep * 20} className="max-w-xs mx-auto" />
                </div>
              </CardContent>
            </Card>
          )}

          {result && (
            <>
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-emerald-600">{result.optimizationScore}%</div>
                    <p className="text-xs text-muted-foreground">Optimization</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className={cn("text-2xl font-bold", result.conflicts > 0 ? "text-amber-600" : "text-emerald-600")}>
                      {result.conflicts}
                    </div>
                    <p className="text-xs text-muted-foreground">Conflicts</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">{result.slots.length}</div>
                    <p className="text-xs text-muted-foreground">Periods</p>
                  </CardContent>
                </Card>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" /> Regenerate
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-1" /> Export
                </Button>
                <Button size="sm">
                  <Check className="h-4 w-4 mr-1" /> Apply Schedule
                </Button>
              </div>

              {/* Generated Schedule Preview */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Generated Schedule - Class {selectedClass}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="py-2 px-3 text-left">Day</th>
                          <th className="py-2 px-3 text-left">Period</th>
                          <th className="py-2 px-3 text-left">Subject</th>
                          <th className="py-2 px-3 text-left">Teacher</th>
                          <th className="py-2 px-3 text-left">Room</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.slots.map((slot, i) => (
                          <motion.tr
                            key={i}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: i * 0.05 }}
                            className={cn(
                              "border-b",
                              slot.hasConflict && "bg-amber-50 dark:bg-amber-900/10"
                            )}
                          >
                            <td className="py-2 px-3">{slot.day}</td>
                            <td className="py-2 px-3">{slot.period}</td>
                            <td className="py-2 px-3 font-medium">{slot.subject}</td>
                            <td className="py-2 px-3">{slot.teacher}</td>
                            <td className="py-2 px-3 flex items-center gap-2">
                              {slot.room}
                              {slot.hasConflict && (
                                <AlertTriangle className="h-4 w-4 text-amber-500" />
                              )}
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* AI Suggestions */}
              {result.suggestions.length > 0 && (
                <Card className="border-blue-200 dark:border-blue-800">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-blue-500" />
                      AI Suggestions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.suggestions.map((suggestion, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Info className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {!isGenerating && !result && (
            <Card>
              <CardContent className="py-16 text-center">
                <Calendar className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="font-semibold mb-2">Ready to Generate</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Configure your constraints and click "Generate Schedule" to create an AI-optimized timetable.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

// Main component with feature gate
const AIScheduleMaker = () => {
  return (
    <FeatureGate feature="schedule-maker">
      <AIScheduleMakerContent />
    </FeatureGate>
  );
};

export default AIScheduleMaker;
