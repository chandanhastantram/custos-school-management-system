import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Check, X, Sparkles, Crown, Zap, ChevronRight, Users, Clock,
  GraduationCap, BarChart3, Calendar, Shield, Palette, Code,
  HeadphonesIcon, Star, ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  TIER_CONFIG, SubscriptionTier, FEATURE_META, AIFeature,
  useSubscriptionStore, getTierColorClasses,
} from "@/store/subscription-store";
import { TierBadge } from "@/components/FeatureGate";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

// Features list with icons
const ALL_FEATURES = [
  { id: "users", name: "Users/Students", icon: Users, basic: "100", pro: "500", max: "Unlimited" },
  { id: "ai-queries", name: "AI Queries/Day", icon: Sparkles, basic: "5", pro: "50", max: "Unlimited" },
  { id: "core", name: "Core Management", icon: GraduationCap, basic: true, pro: true, max: true },
  { id: "attendance", name: "Attendance Tracking", icon: Clock, basic: true, pro: true, max: true },
  { id: "finance", name: "Fee Management", icon: BarChart3, basic: true, pro: true, max: true },
  { id: "reports", name: "Basic Reports", icon: BarChart3, basic: true, pro: true, max: true },
  { id: "ai-assistant", name: "AI Assistant", icon: Sparkles, basic: true, pro: true, max: true },
  { id: "study-trainer", name: "Study Trainer Bot", icon: GraduationCap, basic: false, pro: true, max: true },
  { id: "ai-insights", name: "AI Performance Insights", icon: BarChart3, basic: false, pro: true, max: true },
  { id: "ai-schedule", name: "AI Schedule Maker", icon: Calendar, basic: false, pro: false, max: true },
  { id: "ai-reports", name: "AI Report Generator", icon: BarChart3, basic: false, pro: false, max: true },
  { id: "support", name: "Priority Support", icon: HeadphonesIcon, basic: false, pro: true, max: true },
  { id: "branding", name: "Custom Branding", icon: Palette, basic: false, pro: false, max: true },
  { id: "api", name: "API Access", icon: Code, basic: false, pro: false, max: true },
  { id: "whitelabel", name: "White Label", icon: Shield, basic: false, pro: false, max: true },
];

const PricingPage = () => {
  const { tier: currentTier, setTier } = useSubscriptionStore();
  const [isAnnual, setIsAnnual] = useState(false);
  
  const handleSelectPlan = (tier: SubscriptionTier) => {
    setTier(tier);
    toast({
      title: `Switched to ${TIER_CONFIG[tier].name}`,
      description: tier === "basic" 
        ? "You're now on the free plan" 
        : "Demo mode: Plan activated instantly",
    });
  };

  const getPrice = (tier: SubscriptionTier) => {
    const basePrice = TIER_CONFIG[tier].price;
    if (isAnnual && basePrice > 0) {
      return Math.round(basePrice * 10); // 2 months free
    }
    return basePrice;
  };

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto">
        <Badge className="mb-4" variant="secondary">Pricing</Badge>
        <h1 className="text-3xl font-bold mb-3">
          Choose the perfect plan for your school
        </h1>
        <p className="text-muted-foreground">
          Start free and upgrade as you grow. All plans include core management features.
        </p>
      </div>

      {/* Billing Toggle */}
      <div className="flex items-center justify-center gap-3">
        <Label className={!isAnnual ? "font-semibold" : "text-muted-foreground"}>Monthly</Label>
        <Switch checked={isAnnual} onCheckedChange={setIsAnnual} />
        <Label className={isAnnual ? "font-semibold" : "text-muted-foreground"}>
          Annual <Badge variant="secondary" className="ml-1 text-xs">Save 17%</Badge>
        </Label>
      </div>

      {/* Pricing Cards */}
      <div className="grid gap-6 lg:grid-cols-3 max-w-5xl mx-auto">
        {(["basic", "pro", "max"] as SubscriptionTier[]).map((tier, i) => {
          const config = TIER_CONFIG[tier];
          const isCurrentTier = tier === currentTier;
          const isPopular = tier === "pro";
          const price = getPrice(tier);
          
          return (
            <motion.div
              key={tier}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className={cn(
                "relative h-full flex flex-col",
                isPopular && "border-primary shadow-lg scale-105 z-10",
                isCurrentTier && "ring-2 ring-primary"
              )}>
                {isPopular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-primary">
                      <Star className="h-3 w-3 mr-1 fill-current" /> Most Popular
                    </Badge>
                  </div>
                )}
                {isCurrentTier && (
                  <div className="absolute -top-3 right-4">
                    <Badge variant="outline" className="bg-background">Current Plan</Badge>
                  </div>
                )}
                
                <CardHeader className="text-center pb-2">
                  <div className="flex justify-center mb-2">
                    <div className={cn(
                      "h-12 w-12 rounded-xl flex items-center justify-center",
                      tier === "basic" && "bg-gray-100 dark:bg-gray-800",
                      tier === "pro" && "bg-blue-100 dark:bg-blue-900/30",
                      tier === "max" && "bg-gradient-to-br from-purple-500 to-pink-500"
                    )}>
                      {tier === "basic" && <Users className="h-6 w-6 text-gray-600 dark:text-gray-400" />}
                      {tier === "pro" && <Zap className="h-6 w-6 text-blue-600" />}
                      {tier === "max" && <Crown className="h-6 w-6 text-white" />}
                    </div>
                  </div>
                  <CardTitle className="text-xl">{config.name}</CardTitle>
                  <CardDescription>{config.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">
                      {price === 0 ? "Free" : `₹${price.toLocaleString()}`}
                    </span>
                    {price > 0 && (
                      <span className="text-muted-foreground text-sm">
                        /{isAnnual ? "year" : "month"}
                      </span>
                    )}
                  </div>
                </CardHeader>
                
                <CardContent className="flex-1 flex flex-col">
                  <ul className="space-y-2 flex-1">
                    {ALL_FEATURES.slice(0, tier === "max" ? undefined : tier === "pro" ? 11 : 7).map((feature) => {
                      const value = feature[tier as keyof typeof feature];
                      const hasFeature = value === true || typeof value === "string";
                      
                      return (
                        <li key={feature.id} className="flex items-center gap-2 text-sm">
                          {hasFeature ? (
                            <Check className="h-4 w-4 text-emerald-500 shrink-0" />
                          ) : (
                            <X className="h-4 w-4 text-muted-foreground/40 shrink-0" />
                          )}
                          <span className={!hasFeature ? "text-muted-foreground/60" : ""}>
                            {feature.name}
                            {typeof value === "string" && (
                              <span className="text-muted-foreground ml-1">({value})</span>
                            )}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                  
                  <Button
                    className="w-full mt-6"
                    variant={isCurrentTier ? "outline" : isPopular ? "default" : "secondary"}
                    disabled={isCurrentTier}
                    onClick={() => handleSelectPlan(tier)}
                  >
                    {isCurrentTier ? "Current Plan" : tier === "basic" ? "Start Free" : `Upgrade to ${config.name}`}
                    {!isCurrentTier && <ArrowRight className="h-4 w-4 ml-1" />}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Feature Comparison Table */}
      <div className="max-w-5xl mx-auto mt-12">
        <h2 className="text-xl font-semibold text-center mb-6">Complete Feature Comparison</h2>
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left py-3 px-4 font-medium">Feature</th>
                    <th className="text-center py-3 px-4 font-medium">
                      <TierBadge tier="basic" />
                    </th>
                    <th className="text-center py-3 px-4 font-medium">
                      <TierBadge tier="pro" />
                    </th>
                    <th className="text-center py-3 px-4 font-medium">
                      <TierBadge tier="max" />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {ALL_FEATURES.map((feature, i) => (
                    <tr key={feature.id} className={i % 2 === 0 ? "bg-muted/20" : ""}>
                      <td className="py-3 px-4 flex items-center gap-2">
                        <feature.icon className="h-4 w-4 text-muted-foreground" />
                        {feature.name}
                      </td>
                      {(["basic", "pro", "max"] as const).map((tier) => {
                        const value = feature[tier];
                        return (
                          <td key={tier} className="text-center py-3 px-4">
                            {value === true ? (
                              <Check className="h-5 w-5 text-emerald-500 mx-auto" />
                            ) : value === false ? (
                              <X className="h-5 w-5 text-muted-foreground/30 mx-auto" />
                            ) : (
                              <span className="font-medium">{value}</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* FAQ or CTA */}
      <div className="text-center max-w-2xl mx-auto mt-12">
        <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-200 dark:border-purple-800">
          <CardContent className="py-8">
            <h3 className="text-lg font-semibold mb-2">Need a custom plan?</h3>
            <p className="text-muted-foreground mb-4">
              For large institutions with 1000+ students, contact us for custom pricing.
            </p>
            <Button variant="outline">
              Contact Sales <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PricingPage;
