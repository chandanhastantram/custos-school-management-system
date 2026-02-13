import { create } from "zustand";
import { persist } from "zustand/middleware";

// Subscription tier types
export type SubscriptionTier = "basic" | "pro" | "max";

// AI feature types
export type AIFeature = 
  | "ai-assistant"
  | "study-trainer"
  | "schedule-maker"
  | "ai-insights"
  | "ai-reports"
  | "custom-branding"
  | "api-access"
  | "white-label";

// Tier configuration
export const TIER_CONFIG = {
  basic: {
    name: "Basic",
    price: 0,
    priceLabel: "Free",
    color: "gray",
    limits: {
      users: 100,
      aiQueriesPerDay: 5,
    },
    features: ["ai-assistant"] as AIFeature[],
    description: "Perfect for small schools getting started",
  },
  pro: {
    name: "Pro",
    price: 999,
    priceLabel: "₹999/mo",
    color: "blue",
    limits: {
      users: 500,
      aiQueriesPerDay: 50,
    },
    features: [
      "ai-assistant",
      "study-trainer",
      "ai-insights",
    ] as AIFeature[],
    description: "For growing schools with advanced needs",
  },
  max: {
    name: "Max",
    price: 2499,
    priceLabel: "₹2,499/mo",
    color: "purple",
    limits: {
      users: -1, // Unlimited
      aiQueriesPerDay: -1, // Unlimited
    },
    features: [
      "ai-assistant",
      "study-trainer",
      "schedule-maker",
      "ai-insights",
      "ai-reports",
      "custom-branding",
      "api-access",
      "white-label",
    ] as AIFeature[],
    description: "Enterprise-grade with all features unlocked",
  },
} as const;

// Feature metadata
export const FEATURE_META: Record<AIFeature, { 
  name: string; 
  description: string; 
  minTier: SubscriptionTier;
  icon: string;
}> = {
  "ai-assistant": {
    name: "AI Assistant",
    description: "General AI-powered help and queries",
    minTier: "basic",
    icon: "sparkles",
  },
  "study-trainer": {
    name: "Study Trainer Bot",
    description: "AI tutoring with practice questions and explanations",
    minTier: "pro",
    icon: "graduation-cap",
  },
  "schedule-maker": {
    name: "AI Schedule Maker",
    description: "Intelligent timetable generation with conflict detection",
    minTier: "max",
    icon: "calendar",
  },
  "ai-insights": {
    name: "AI Performance Insights",
    description: "Student at-risk detection and trend analysis",
    minTier: "pro",
    icon: "trending-up",
  },
  "ai-reports": {
    name: "AI Report Generator",
    description: "Automated report generation and analytics",
    minTier: "max",
    icon: "file-text",
  },
  "custom-branding": {
    name: "Custom Branding",
    description: "Add your school's logo and colors",
    minTier: "max",
    icon: "palette",
  },
  "api-access": {
    name: "API Access",
    description: "Integrate CUSTOS with external systems",
    minTier: "max",
    icon: "plug",
  },
  "white-label": {
    name: "White Label",
    description: "Remove CUSTOS branding completely",
    minTier: "max",
    icon: "tag",
  },
};

interface SubscriptionState {
  // Current subscription
  tier: SubscriptionTier;
  
  // Usage tracking
  aiQueriesUsedToday: number;
  lastQueryDate: string;
  
  // Actions
  setTier: (tier: SubscriptionTier) => void;
  incrementAIQuery: () => boolean; // Returns false if limit reached
  hasFeature: (feature: AIFeature) => boolean;
  getQueryLimit: () => number;
  getRemainingQueries: () => number;
  resetDailyQueries: () => void;
}

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      // Initial state - demo mode uses Pro for showcase
      tier: "pro",
      aiQueriesUsedToday: 0,
      lastQueryDate: new Date().toDateString(),
      
      setTier: (tier) => set({ tier }),
      
      incrementAIQuery: () => {
        const state = get();
        const today = new Date().toDateString();
        
        // Reset if new day
        if (state.lastQueryDate !== today) {
          set({ aiQueriesUsedToday: 0, lastQueryDate: today });
        }
        
        const limit = TIER_CONFIG[state.tier].limits.aiQueriesPerDay;
        
        // -1 means unlimited
        if (limit === -1) {
          set((s) => ({ aiQueriesUsedToday: s.aiQueriesUsedToday + 1 }));
          return true;
        }
        
        if (state.aiQueriesUsedToday >= limit) {
          return false; // Limit reached
        }
        
        set((s) => ({ aiQueriesUsedToday: s.aiQueriesUsedToday + 1 }));
        return true;
      },
      
      hasFeature: (feature) => {
        const state = get();
        return TIER_CONFIG[state.tier].features.includes(feature);
      },
      
      getQueryLimit: () => {
        const state = get();
        return TIER_CONFIG[state.tier].limits.aiQueriesPerDay;
      },
      
      getRemainingQueries: () => {
        const state = get();
        const limit = TIER_CONFIG[state.tier].limits.aiQueriesPerDay;
        if (limit === -1) return -1; // Unlimited
        return Math.max(0, limit - state.aiQueriesUsedToday);
      },
      
      resetDailyQueries: () => {
        set({ aiQueriesUsedToday: 0, lastQueryDate: new Date().toDateString() });
      },
    }),
    {
      name: "custos-subscription",
    }
  )
);

// Helper function to get tier color classes
export const getTierColorClasses = (tier: SubscriptionTier) => {
  switch (tier) {
    case "basic":
      return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
    case "pro":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
    case "max":
      return "bg-gradient-to-r from-purple-500 to-pink-500 text-white";
  }
};
