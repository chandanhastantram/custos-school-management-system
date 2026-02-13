import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import {
  MessageSquare, Search, MoreHorizontal, Send, Paperclip, Smile,
  Phone, Video, Info, Check, CheckCheck, Image, File, Users,
  ArrowLeft, Plus, Star, Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// Types
interface Conversation {
  id: string;
  name: string;
  avatar?: string;
  lastMessage: string;
  time: string;
  unread: number;
  online: boolean;
  isGroup?: boolean;
}

interface Message {
  id: string;
  senderId: string;
  content: string;
  time: string;
  status: "sent" | "delivered" | "read";
  type: "text" | "image" | "file";
}

// Demo data
const DEMO_CONVERSATIONS: Conversation[] = [
  { id: "1", name: "Mrs. Sharma (Class Teacher)", lastMessage: "Aisha has been performing well in Mathematics", time: "10:30 AM", unread: 2, online: true },
  { id: "2", name: "Mr. Patel (Science)", lastMessage: "The lab report is due tomorrow", time: "Yesterday", unread: 0, online: false },
  { id: "3", name: "Class 10-A Parents", lastMessage: "Meeting scheduled for Dec 20", time: "Yesterday", unread: 5, online: false, isGroup: true },
  { id: "4", name: "School Admin", lastMessage: "Fee payment reminder sent", time: "2 days ago", unread: 0, online: true },
  { id: "5", name: "Mrs. Verma (English)", lastMessage: "Essay submission deadline extended", time: "3 days ago", unread: 0, online: false },
];

const DEMO_MESSAGES: Message[] = [
  { id: "1", senderId: "other", content: "Good morning! I wanted to discuss Aisha's performance in the recent unit test.", time: "10:15 AM", status: "read", type: "text" },
  { id: "2", senderId: "me", content: "Good morning Mrs. Sharma! Yes, please go ahead.", time: "10:18 AM", status: "read", type: "text" },
  { id: "3", senderId: "other", content: "Aisha has been performing exceptionally well in Mathematics. She scored 92/100 in the recent test.", time: "10:20 AM", status: "read", type: "text" },
  { id: "4", senderId: "other", content: "I'm particularly impressed with her problem-solving skills in algebra.", time: "10:22 AM", status: "read", type: "text" },
  { id: "5", senderId: "me", content: "That's wonderful to hear! We've been practicing extra at home.", time: "10:25 AM", status: "read", type: "text" },
  { id: "6", senderId: "other", content: "Keep up the good work! I'll send you some additional practice problems that might help her prepare for the finals.", time: "10:28 AM", status: "read", type: "text" },
  { id: "7", senderId: "other", content: "Also, there's a parent-teacher meeting scheduled for December 20th. Please confirm your attendance.", time: "10:30 AM", status: "delivered", type: "text" },
];

const MessagesPage = () => {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(DEMO_CONVERSATIONS[0]);
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [isMobileView, setIsMobileView] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [DEMO_MESSAGES]);

  const handleSend = () => {
    if (!message.trim()) return;
    // Demo: just clear the message
    setMessage("");
  };

  const filteredConversations = DEMO_CONVERSATIONS.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-[calc(100vh-8rem)] flex rounded-xl border border-border bg-card overflow-hidden">
      {/* Conversations List */}
      <div className={cn(
        "w-80 border-r border-border flex flex-col",
        selectedConversation && isMobileView ? "hidden md:flex" : "flex"
      )}>
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Messages</h2>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Conversation List */}
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {filteredConversations.map((conv) => (
              <motion.div
                key={conv.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={cn(
                  "p-3 rounded-lg cursor-pointer transition-colors",
                  selectedConversation?.id === conv.id
                    ? "bg-primary/10"
                    : "hover:bg-muted/50"
                )}
                onClick={() => setSelectedConversation(conv)}
              >
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className={cn(
                        "text-sm",
                        conv.isGroup ? "bg-purple-100 text-purple-600" : "bg-primary/10 text-primary"
                      )}>
                        {conv.isGroup ? <Users className="h-4 w-4" /> : conv.name.split(" ").map(n => n[0]).slice(0, 2).join("")}
                      </AvatarFallback>
                    </Avatar>
                    {conv.online && !conv.isGroup && (
                      <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-background" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm truncate">{conv.name}</p>
                      <span className="text-xs text-muted-foreground">{conv.time}</span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <p className="text-xs text-muted-foreground truncate pr-2">{conv.lastMessage}</p>
                      {conv.unread > 0 && (
                        <Badge className="h-5 w-5 rounded-full p-0 flex items-center justify-center text-[10px]">
                          {conv.unread}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Chat Area */}
      {selectedConversation ? (
        <div className={cn(
          "flex-1 flex flex-col",
          !selectedConversation && isMobileView ? "hidden md:flex" : "flex"
        )}>
          {/* Chat Header */}
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden h-8 w-8"
                onClick={() => setSelectedConversation(null)}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <Avatar className="h-10 w-10">
                <AvatarFallback className="bg-primary/10 text-primary text-sm">
                  {selectedConversation.name.split(" ").map(n => n[0]).slice(0, 2).join("")}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium text-sm">{selectedConversation.name}</p>
                <p className="text-xs text-muted-foreground">
                  {selectedConversation.online ? (
                    <span className="text-emerald-600">Online</span>
                  ) : (
                    "Last seen recently"
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Phone className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Video className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Info className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {DEMO_MESSAGES.map((msg, i) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className={cn(
                    "flex",
                    msg.senderId === "me" ? "justify-end" : "justify-start"
                  )}
                >
                  <div className={cn(
                    "max-w-[70%] rounded-2xl px-4 py-2",
                    msg.senderId === "me"
                      ? "bg-primary text-primary-foreground rounded-br-sm"
                      : "bg-muted rounded-bl-sm"
                  )}>
                    <p className="text-sm">{msg.content}</p>
                    <div className={cn(
                      "flex items-center gap-1 mt-1 text-[10px]",
                      msg.senderId === "me" ? "justify-end text-primary-foreground/70" : "text-muted-foreground"
                    )}>
                      <span>{msg.time}</span>
                      {msg.senderId === "me" && (
                        msg.status === "read" ? (
                          <CheckCheck className="h-3 w-3 text-blue-400" />
                        ) : (
                          <Check className="h-3 w-3" />
                        )
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Message Input */}
          <div className="p-4 border-t border-border">
            <div className="flex items-end gap-2">
              <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0">
                <Paperclip className="h-4 w-4" />
              </Button>
              <div className="flex-1 relative">
                <Textarea
                  placeholder="Type a message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  className="min-h-[40px] max-h-[120px] resize-none pr-10"
                  rows={1}
                />
                <Button variant="ghost" size="icon" className="absolute right-1 bottom-1 h-7 w-7">
                  <Smile className="h-4 w-4" />
                </Button>
              </div>
              <Button size="icon" className="h-9 w-9 shrink-0" onClick={handleSend}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>Select a conversation to start messaging</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessagesPage;
