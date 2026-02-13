import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  GraduationCap, Send, Loader2, User, Bot, BookOpen, Brain,
  Lightbulb, HelpCircle, Sparkles, ChevronRight, Clock, Award,
  Check, X, RotateCcw, Volume2, Copy, ThumbsUp, ThumbsDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { FeatureGate, ProBadge } from "@/components/FeatureGate";
import { useAIQueryLimit } from "@/hooks/useFeatureGate";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Types
interface Message {
  id: string;
  role: "user" | "tutor";
  content: string;
  type: "text" | "question" | "explanation" | "practice";
  timestamp: Date;
}

interface Subject {
  id: string;
  name: string;
  icon: string;
  topics: string[];
}

interface StudySession {
  subject: string;
  topic: string;
  startTime: Date;
  questionsAnswered: number;
  correctAnswers: number;
}

// Demo data
const SUBJECTS: Subject[] = [
  { id: "math", name: "Mathematics", icon: "📐", topics: ["Algebra", "Geometry", "Calculus", "Trigonometry", "Statistics"] },
  { id: "physics", name: "Physics", icon: "⚛️", topics: ["Mechanics", "Thermodynamics", "Optics", "Electricity", "Modern Physics"] },
  { id: "chemistry", name: "Chemistry", icon: "🧪", topics: ["Organic", "Inorganic", "Physical", "Biochemistry"] },
  { id: "biology", name: "Biology", icon: "🧬", topics: ["Cell Biology", "Genetics", "Ecology", "Human Anatomy"] },
  { id: "english", name: "English", icon: "📚", topics: ["Grammar", "Literature", "Writing", "Vocabulary"] },
  { id: "history", name: "History", icon: "🏛️", topics: ["Ancient", "Medieval", "Modern", "World Wars"] },
];

const DEMO_RESPONSES: Record<string, string> = {
  algebra: `Great question! Let me explain **Quadratic Equations** step by step.

## What is a Quadratic Equation?
A quadratic equation is a polynomial equation of degree 2, in the form:
**ax² + bx + c = 0**

Where a, b, and c are constants, and a ≠ 0.

## How to Solve?
There are 3 main methods:
1. **Factoring** - When the equation can be factored
2. **Quadratic Formula** - x = (-b ± √(b²-4ac)) / 2a
3. **Completing the Square**

### Example
Solve: x² - 5x + 6 = 0

**Solution:**
- Factor: (x-2)(x-3) = 0
- x = 2 or x = 3

Would you like me to give you a practice problem?`,

  practice: `## 📝 Practice Question

**Solve the quadratic equation:**
x² - 7x + 12 = 0

**Options:**
A) x = 3, x = 4
B) x = 2, x = 6
C) x = 1, x = 12
D) x = -3, x = -4

Take your time and try to solve it! Click on your answer when ready.`,

  correct: `## ✅ Correct! Excellent work!

**x² - 7x + 12 = 0**

You factored it correctly:
(x - 3)(x - 4) = 0

So x = 3 or x = 4

### Key Insight:
Always check if two numbers:
- Multiply to give c (12)
- Add to give b (-7)

Here: -3 × -4 = 12 and -3 + -4 = -7 ✓

**Your accuracy: 85%** 📈

Ready for another question?`,

  wrong: `## ❌ Not quite! Let's work through this together.

**x² - 7x + 12 = 0**

To factor, we need two numbers that:
- Multiply to give 12
- Add to give -7

Let's try: -3 and -4
- (-3) × (-4) = 12 ✓
- (-3) + (-4) = -7 ✓

So: (x - 3)(x - 4) = 0
**x = 3 or x = 4**

The correct answer was **A**.

Would you like me to explain this differently, or try another problem?`,
};

const StudyTrainerContent = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [session, setSession] = useState<StudySession | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { canQuery, useQuery, usageText } = useAIQueryLimit();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startSession = (subject: string, topic: string) => {
    setSelectedSubject(subject);
    setSelectedTopic(topic);
    setSession({
      subject,
      topic,
      startTime: new Date(),
      questionsAnswered: 0,
      correctAnswers: 0,
    });
    
    // Welcome message
    const welcomeMsg: Message = {
      id: Date.now().toString(),
      role: "tutor",
      content: `# Welcome to ${topic} Practice! 🎓

I'm your AI Study Trainer. I'll help you master **${topic}** in **${SUBJECTS.find(s => s.id === subject)?.name}**.

## How this works:
1. Ask me any question about the topic
2. I'll explain concepts clearly
3. I'll give you practice problems
4. Track your progress

**Let's start!** What would you like to learn about ${topic}?`,
      type: "text",
      timestamp: new Date(),
    };
    setMessages([welcomeMsg]);
  };

  const handleSend = async (customMessage?: string) => {
    const messageText = customMessage || input.trim();
    if (!messageText || isLoading) return;

    if (!canQuery) {
      toast({
        title: "Query limit reached",
        description: "Upgrade your plan for more AI queries",
        variant: "destructive",
      });
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      type: "text",
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    useQuery();

    // Simulate AI response
    setTimeout(() => {
      let response = DEMO_RESPONSES.algebra;
      let msgType: Message["type"] = "explanation";
      
      if (messageText.toLowerCase().includes("practice") || messageText.toLowerCase().includes("question")) {
        response = DEMO_RESPONSES.practice;
        msgType = "question";
      } else if (messageText.toLowerCase().includes("a)") || messageText === "A") {
        response = DEMO_RESPONSES.correct;
        msgType = "text";
        if (session) {
          setSession({
            ...session,
            questionsAnswered: session.questionsAnswered + 1,
            correctAnswers: session.correctAnswers + 1,
          });
        }
      } else if (messageText.match(/^[bcd]\)?$/i)) {
        response = DEMO_RESPONSES.wrong;
        msgType = "text";
        if (session) {
          setSession({
            ...session,
            questionsAnswered: session.questionsAnswered + 1,
          });
        }
      }

      const tutorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "tutor",
        content: response,
        type: msgType,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, tutorMessage]);
      setIsLoading(false);
    }, 1500);
  };

  // Subject selection view
  if (!selectedSubject) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold">Study Trainer</h1>
                <ProBadge />
              </div>
              <p className="text-muted-foreground text-sm">AI-powered tutoring for every subject</p>
            </div>
          </div>
          <Badge variant="outline">{usageText}</Badge>
        </div>

        {/* Subject Grid */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Choose a Subject</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {SUBJECTS.map((subject, i) => (
              <motion.div
                key={subject.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card 
                  className="cursor-pointer hover:shadow-lg hover:border-primary/50 transition-all"
                  onClick={() => setSelectedSubject(subject.id)}
                >
                  <CardContent className="p-4">
                    <div className="text-3xl mb-2">{subject.icon}</div>
                    <h3 className="font-semibold">{subject.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      {subject.topics.length} topics available
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {subject.topics.slice(0, 3).map(topic => (
                        <Badge key={topic} variant="secondary" className="text-xs">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Study Tips */}
        <Card className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Lightbulb className="h-5 w-5 text-amber-500 mt-0.5" />
              <div>
                <h4 className="font-medium">Study Tips</h4>
                <ul className="text-sm text-muted-foreground mt-1 space-y-1">
                  <li>• Ask specific questions for better explanations</li>
                  <li>• Request practice problems to test your understanding</li>
                  <li>• Don't hesitate to ask "explain it differently"</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Topic selection view
  if (!selectedTopic) {
    const subject = SUBJECTS.find(s => s.id === selectedSubject)!;
    
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setSelectedSubject(null)}>
            ← Back
          </Button>
          <h1 className="text-xl font-bold">{subject.icon} {subject.name}</h1>
        </div>
        
        <h2 className="text-lg font-semibold">Choose a Topic</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {subject.topics.map((topic, i) => (
            <motion.div
              key={topic}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card 
                className="cursor-pointer hover:shadow-md hover:border-primary/50 transition-all"
                onClick={() => startSession(selectedSubject, topic)}
              >
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BookOpen className="h-5 w-5 text-primary" />
                    <span className="font-medium">{topic}</span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  // Chat view
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Session Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => {
            setSelectedTopic(null);
            setMessages([]);
            setSession(null);
          }}>
            ← Back
          </Button>
          <div>
            <h2 className="font-semibold">{selectedTopic}</h2>
            <p className="text-xs text-muted-foreground">{SUBJECTS.find(s => s.id === selectedSubject)?.name}</p>
          </div>
        </div>
        {session && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span>{Math.round((Date.now() - session.startTime.getTime()) / 60000)} min</span>
            </div>
            <div className="flex items-center gap-1">
              <Award className="h-4 w-4 text-amber-500" />
              <span>{session.correctAnswers}/{session.questionsAnswered}</span>
            </div>
          </div>
        )}
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}
              >
                {msg.role === "tutor" && (
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shrink-0">
                    <Brain className="h-4 w-4 text-white" />
                  </div>
                )}
                <div className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3",
                  msg.role === "user" 
                    ? "bg-primary text-primary-foreground" 
                    : "bg-muted"
                )}>
                  <div 
                    className="prose prose-sm dark:prose-invert max-w-none"
                    dangerouslySetInnerHTML={{ 
                      __html: msg.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br>')
                        .replace(/# (.*?)(?=\n|$)/g, '<h2 class="text-lg font-bold mt-2 mb-1">$1</h2>')
                        .replace(/## (.*?)(?=\n|$)/g, '<h3 class="text-base font-semibold mt-2 mb-1">$1</h3>')
                        .replace(/### (.*?)(?=\n|$)/g, '<h4 class="text-sm font-medium mt-1">$1</h4>')
                    }} 
                  />
                </div>
                {msg.role === "user" && (
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                )}
              </motion.div>
            ))}
            {isLoading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <Brain className="h-4 w-4 text-white" />
                </div>
                <div className="bg-muted rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Quick Actions */}
        <div className="px-4 pt-2 border-t flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => handleSend("Give me a practice question")}>
            <HelpCircle className="h-3.5 w-3.5 mr-1" /> Practice Question
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleSend("Explain this concept differently")}>
            <RotateCcw className="h-3.5 w-3.5 mr-1" /> Explain Differently
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleSend("Give me tips to remember this")}>
            <Lightbulb className="h-3.5 w-3.5 mr-1" /> Memory Tips
          </Button>
        </div>

        {/* Input */}
        <div className="p-4 border-t">
          <div className="flex items-end gap-2">
            <Textarea
              placeholder="Ask a question or type an answer..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="min-h-[44px] max-h-[120px] resize-none"
              rows={1}
            />
            <Button
              size="icon"
              className="h-11 w-11 shrink-0"
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

// Main page with feature gate
const StudyTrainerPage = () => {
  return (
    <FeatureGate feature="study-trainer">
      <StudyTrainerContent />
    </FeatureGate>
  );
};

export default StudyTrainerPage;
