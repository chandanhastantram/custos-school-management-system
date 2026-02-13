import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, Send, Loader2, User, Bot, Copy, ThumbsUp, ThumbsDown,
  RefreshCw, Lightbulb, BookOpen, Calculator, HelpCircle, Calendar,
  FileText, BarChart3, Trash2, History,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { TierBadge, UpgradeModal } from "@/components/FeatureGate";
import { useAIQueryLimit } from "@/hooks/useFeatureGate";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Types
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface SuggestedPrompt {
  icon: React.ElementType;
  title: string;
  prompt: string;
  color: string;
}

// Demo suggestions
const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  { icon: BarChart3, title: "Analyze Performance", prompt: "Analyze the class performance trends for Class 10-A this semester", color: "text-blue-600 bg-blue-100" },
  { icon: Calendar, title: "Schedule Events", prompt: "Help me plan the parent-teacher meeting for next week", color: "text-purple-600 bg-purple-100" },
  { icon: Calculator, title: "Fee Calculations", prompt: "Calculate the total pending fees for Class 9", color: "text-amber-600 bg-amber-100" },
  { icon: FileText, title: "Generate Report", prompt: "Generate a monthly attendance summary report", color: "text-emerald-600 bg-emerald-100" },
  { icon: Lightbulb, title: "Teaching Tips", prompt: "Suggest engaging activities for teaching quadratic equations", color: "text-rose-600 bg-rose-100" },
  { icon: HelpCircle, title: "System Help", prompt: "How do I export student data to Excel?", color: "text-cyan-600 bg-cyan-100" },
];

const DEMO_RESPONSES: Record<string, string> = {
  "default": `I'm **CUSTOS AI Assistant**, here to help you with:

- 📊 **Analytics & Reports** - Performance analysis, attendance trends
- 📅 **Scheduling** - Timetables, meetings, events
- 💰 **Finance** - Fee calculations, payment tracking
- 📝 **Academic** - Lesson planning, curriculum queries
- 🔧 **System Help** - Navigation, features, troubleshooting

What would you like help with today?`,
  "performance": `## Class 10-A Performance Analysis

Based on the mid-term examination data:

### Key Insights
- **Average Score**: 78.5% (↑5% from last exam)
- **Top Performer**: Aisha Sharma (94.5%)
- **Pass Rate**: 97%

### Subject-wise Breakdown
| Subject | Avg Score | Trend |
|---------|----------|-------|
| Mathematics | 82% | ↑ |
| Science | 78% | ↑ |
| English | 75% | → |

### Recommendations
1. Focus on English writing skills
2. Continue math enrichment activities
3. Consider peer tutoring for struggling students`,
  "meeting": `## Parent-Teacher Meeting Plan

### Suggested Schedule
- **Date**: December 20, 2024
- **Time**: 9:00 AM - 1:00 PM
- **Venue**: School Auditorium

### Agenda
1. Welcome address (15 min)
2. Academic progress review (45 min)
3. Break (15 min)
4. Individual parent slots (2 hrs)

### Action Items
- [ ] Send invitations to parents
- [ ] Prepare progress reports
- [ ] Set up appointment slots

Would you like me to draft the invitation message?`,
};

const AIAssistantPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const { tier, canQuery, useQuery, usageText, remaining, isUnlimited } = useAIQueryLimit();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (prompt?: string) => {
    const messageText = prompt || input.trim();
    if (!messageText || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Check query limit
    if (!canQuery) {
      toast({
        title: "Daily limit reached",
        description: "Upgrade your plan for more AI queries",
        variant: "destructive",
      });
      setShowUpgrade(true);
      setIsLoading(false);
      return;
    }
    useQuery();

    // Simulate AI response
    setTimeout(() => {
      let response = DEMO_RESPONSES.default;
      if (messageText.toLowerCase().includes("performance") || messageText.toLowerCase().includes("analyze")) {
        response = DEMO_RESPONSES.performance;
      } else if (messageText.toLowerCase().includes("meeting") || messageText.toLowerCase().includes("schedule")) {
        response = DEMO_RESPONSES.meeting;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({ title: "Copied to clipboard" });
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
        <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AI Assistant</h1>
            <p className="text-xs text-muted-foreground">Powered by CUSTOS Intelligence</p>
          </div>
          <TierBadge tier={tier} size="sm" />
        </div>
        <div className="flex items-center gap-2">
          <Badge 
            variant={remaining <= 2 && !isUnlimited ? "destructive" : "outline"} 
            className="text-xs cursor-pointer"
            onClick={() => setShowUpgrade(true)}
          >
            {usageText}
          </Badge>
          {messages.length > 0 && (
            <Button variant="outline" size="sm" onClick={clearChat}>
              <Trash2 className="h-4 w-4 mr-1" /> Clear
            </Button>
          )}
        </div>
      </div>

      <UpgradeModal open={showUpgrade} onClose={() => setShowUpgrade(false)} />

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-8">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-4">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-lg font-semibold mb-2">How can I help you today?</h2>
              <p className="text-sm text-muted-foreground mb-6 max-w-md">
                I can help with analytics, scheduling, reports, and answer questions about the school management system.
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 max-w-3xl">
                {SUGGESTED_PROMPTS.map((suggestion, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <Card
                      className="cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => handleSend(suggestion.prompt)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={cn("h-7 w-7 rounded-lg flex items-center justify-center", suggestion.color)}>
                            <suggestion.icon className="h-4 w-4" />
                          </div>
                          <span className="font-medium text-sm">{suggestion.title}</span>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">{suggestion.prompt}</p>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, i) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn("flex gap-3", message.role === "user" ? "justify-end" : "justify-start")}
                >
                  {message.role === "assistant" && (
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shrink-0">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  <div className={cn(
                    "max-w-[80%] rounded-2xl px-4 py-3",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {message.role === "assistant" ? (
                        <div dangerouslySetInnerHTML={{ 
                          __html: message.content
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\n/g, '<br>')
                            .replace(/## (.*?)(?=\n|$)/g, '<h3 class="text-base font-semibold mt-3 mb-2">$1</h3>')
                            .replace(/### (.*?)(?=\n|$)/g, '<h4 class="text-sm font-medium mt-2 mb-1">$1</h4>')
                        }} />
                      ) : (
                        <p className="text-sm m-0">{message.content}</p>
                      )}
                    </div>
                    {message.role === "assistant" && (
                      <div className="flex items-center gap-1 mt-3 pt-2 border-t border-border/50">
                        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleCopy(message.content)}>
                          <Copy className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7">
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7">
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7">
                          <RefreshCw className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  {message.role === "user" && (
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <User className="h-4 w-4 text-primary" />
                    </div>
                  )}
                </motion.div>
              ))}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3"
                >
                  <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="bg-muted rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 border-t">
          <div className="flex items-end gap-2">
            <Textarea
              ref={textareaRef}
              placeholder="Ask me anything..."
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
          <p className="text-xs text-muted-foreground text-center mt-2">
            AI responses are for assistance only. Always verify important information.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default AIAssistantPage;
