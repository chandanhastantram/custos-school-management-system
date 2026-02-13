import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, AlertTriangle, Users, Award, Clock,
  ChevronRight, Sparkles, ArrowUpRight, ArrowDownRight, Eye,
  BookOpen, Target, Bell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ProBadge } from "@/components/FeatureGate";
import { useFeatureGate } from "@/hooks/useFeatureGate";
import { cn } from "@/lib/utils";

// Types
interface StudentRisk {
  id: string;
  name: string;
  class: string;
  riskLevel: "high" | "medium" | "low";
  factors: string[];
  trend: "up" | "down" | "stable";
  score: number;
}

interface ClassInsight {
  class: string;
  subject: string;
  insight: string;
  type: "positive" | "warning" | "info";
  metric: string;
}

interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  category: string;
}

// Demo data
const AT_RISK_STUDENTS: StudentRisk[] = [
  { id: "1", name: "Rahul Sharma", class: "10-A", riskLevel: "high", factors: ["Low attendance", "Declining grades"], trend: "down", score: 35 },
  { id: "2", name: "Priya Patel", class: "9-B", riskLevel: "medium", factors: ["Missing assignments"], trend: "stable", score: 55 },
  { id: "3", name: "Amit Kumar", class: "10-A", riskLevel: "medium", factors: ["Exam performance drop"], trend: "down", score: 58 },
];

const CLASS_INSIGHTS: ClassInsight[] = [
  { class: "10-A", subject: "Mathematics", insight: "Class average improved by 12% this month", type: "positive", metric: "+12%" },
  { class: "9-B", subject: "Science", insight: "5 students below passing threshold", type: "warning", metric: "5 students" },
  { class: "11-A", subject: "Physics", insight: "Lab attendance is 15% lower than theory", type: "info", metric: "-15%" },
];

const RECOMMENDATIONS: Recommendation[] = [
  { id: "1", title: "Schedule parent meeting for at-risk students", description: "3 students in 10-A need intervention", priority: "high", category: "intervention" },
  { id: "2", title: "Consider remedial classes for Science", description: "Class 9-B showing consistent struggles", priority: "medium", category: "academic" },
  { id: "3", title: "Recognize top performers", description: "5 students improved by 20%+ this month", priority: "low", category: "motivation" },
];

interface AIInsightsProps {
  compact?: boolean;
  showStudentRisks?: boolean;
  showClassInsights?: boolean;
  showRecommendations?: boolean;
}

const AIInsights = ({
  compact = false,
  showStudentRisks = true,
  showClassInsights = true,
  showRecommendations = true,
}: AIInsightsProps) => {
  const { allowed } = useFeatureGate("ai-insights");
  const [expandedStudent, setExpandedStudent] = useState<string | null>(null);

  if (!allowed) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-8 text-center">
          <Sparkles className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
          <h3 className="font-medium mb-1">AI Insights</h3>
          <p className="text-sm text-muted-foreground mb-3">
            Get AI-powered analytics and recommendations
          </p>
          <ProBadge />
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card className="bg-gradient-to-br from-purple-500/5 to-pink-500/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              AI Insights
            </CardTitle>
            <ProBadge />
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {AT_RISK_STUDENTS.slice(0, 2).map((student) => (
            <div key={student.id} className="flex items-center justify-between text-sm">
              <span>{student.name}</span>
              <Badge variant={student.riskLevel === "high" ? "destructive" : "secondary"} className="text-[10px]">
                {student.riskLevel}
              </Badge>
            </div>
          ))}
          <Button variant="ghost" size="sm" className="w-full mt-2">
            View All <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold">AI Performance Insights</h2>
          <ProBadge />
        </div>
        <Badge variant="outline" className="text-xs">
          Updated 5 min ago
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* At-Risk Students */}
        {showStudentRisks && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Students At Risk
                </CardTitle>
                <Badge variant="secondary">{AT_RISK_STUDENTS.length}</Badge>
              </div>
              <CardDescription>Students requiring immediate attention</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {AT_RISK_STUDENTS.map((student) => (
                <motion.div
                  key={student.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border rounded-lg p-3 hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => setExpandedStudent(
                    expandedStudent === student.id ? null : student.id
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-9 w-9">
                        <AvatarFallback className={cn(
                          student.riskLevel === "high" && "bg-red-100 text-red-700",
                          student.riskLevel === "medium" && "bg-amber-100 text-amber-700",
                        )}>
                          {student.name.split(" ").map(n => n[0]).join("")}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-sm">{student.name}</p>
                        <p className="text-xs text-muted-foreground">Class {student.class}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {student.trend === "down" && (
                        <ArrowDownRight className="h-4 w-4 text-red-500" />
                      )}
                      {student.trend === "up" && (
                        <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                      )}
                      <Badge variant={
                        student.riskLevel === "high" ? "destructive" : "secondary"
                      }>
                        {student.score}%
                      </Badge>
                    </div>
                  </div>
                  {expandedStudent === student.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      className="mt-3 pt-3 border-t"
                    >
                      <p className="text-xs text-muted-foreground mb-2">Risk factors:</p>
                      <div className="flex flex-wrap gap-1">
                        {student.factors.map((factor, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {factor}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex gap-2 mt-3">
                        <Button size="sm" variant="outline">
                          <Eye className="h-3.5 w-3.5 mr-1" /> View Details
                        </Button>
                        <Button size="sm">
                          <Bell className="h-3.5 w-3.5 mr-1" /> Alert Parent
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Class Insights */}
        {showClassInsights && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-blue-500" />
                Class Performance
              </CardTitle>
              <CardDescription>Key insights across classes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {CLASS_INSIGHTS.map((insight, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={cn(
                    "border rounded-lg p-3",
                    insight.type === "positive" && "border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-900/10",
                    insight.type === "warning" && "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/10",
                    insight.type === "info" && "border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-900/10",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {insight.class}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {insight.subject}
                        </Badge>
                      </div>
                      <p className="text-sm">{insight.insight}</p>
                    </div>
                    <div className={cn(
                      "text-sm font-semibold shrink-0",
                      insight.type === "positive" && "text-emerald-600",
                      insight.type === "warning" && "text-amber-600",
                      insight.type === "info" && "text-blue-600",
                    )}>
                      {insight.metric}
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recommendations */}
      {showRecommendations && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-500" />
              AI Recommendations
            </CardTitle>
            <CardDescription>Suggested actions based on data analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              {RECOMMENDATIONS.map((rec, i) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="border rounded-lg p-3 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={
                      rec.priority === "high" ? "destructive" :
                      rec.priority === "medium" ? "default" : "secondary"
                    } className="text-[10px]">
                      {rec.priority}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {rec.category}
                    </Badge>
                  </div>
                  <h4 className="font-medium text-sm mb-1">{rec.title}</h4>
                  <p className="text-xs text-muted-foreground">{rec.description}</p>
                  <Button variant="link" size="sm" className="px-0 mt-2">
                    Take Action <ChevronRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIInsights;
