import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Sparkles, Crown, Zap, ChevronRight, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { useFeatureGate } from "@/hooks/useFeatureGate";
import { 
  AIFeature, TIER_CONFIG, SubscriptionTier, FEATURE_META,
  useSubscriptionStore, getTierColorClasses 
} from "@/store/subscription-store";
import { cn } from "@/lib/utils";

interface FeatureGateProps {
  feature: AIFeature;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

/**
 * Component that gates access to features based on subscription tier
 */
export function FeatureGate({ 
  feature, 
  children, 
  fallback,
  showUpgradePrompt = true 
}: FeatureGateProps) {
  const { allowed, requiredTier, featureName } = useFeatureGate(feature);
  const [showModal, setShowModal] = useState(false);
  
  if (allowed) {
    return <>{children}</>;
  }
  
  if (fallback) {
    return <>{fallback}</>;
  }
  
  if (!showUpgradePrompt) {
    return null;
  }
  
  return (
    <>
      <LockedFeatureCard 
        featureName={featureName}
        requiredTier={requiredTier}
        onUpgrade={() => setShowModal(true)}
      />
      <UpgradeModal 
        open={showModal} 
        onClose={() => setShowModal(false)}
        highlightTier={requiredTier}
      />
    </>
  );
}

interface LockedFeatureCardProps {
  featureName: string;
  requiredTier: SubscriptionTier;
  onUpgrade: () => void;
}

function LockedFeatureCard({ featureName, requiredTier, onUpgrade }: LockedFeatureCardProps) {
  const tierConfig = TIER_CONFIG[requiredTier];
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center min-h-[400px] p-8 rounded-xl border-2 border-dashed border-muted-foreground/30 bg-muted/20"
    >
      <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
        <Lock className="h-8 w-8 text-primary" />
      </div>
      <h3 className="text-xl font-bold mb-2">{featureName}</h3>
      <p className="text-muted-foreground text-center mb-4 max-w-md">
        This feature is available in the <span className="font-semibold">{tierConfig.name}</span> plan and above.
      </p>
      <Badge className={cn("mb-4", getTierColorClasses(requiredTier))}>
        {requiredTier === "pro" ? <Zap className="h-3 w-3 mr-1" /> : <Crown className="h-3 w-3 mr-1" />}
        {tierConfig.name} Feature
      </Badge>
      <Button onClick={onUpgrade} className="gap-2">
        <Sparkles className="h-4 w-4" />
        Upgrade to {tierConfig.name}
        <ChevronRight className="h-4 w-4" />
      </Button>
    </motion.div>
  );
}

interface UpgradeModalProps {
  open: boolean;
  onClose: () => void;
  highlightTier?: SubscriptionTier;
}

export function UpgradeModal({ open, onClose, highlightTier = "pro" }: UpgradeModalProps) {
  const { tier: currentTier, setTier } = useSubscriptionStore();
  
  const handleUpgrade = (tier: SubscriptionTier) => {
    // In demo mode, just switch the tier
    setTier(tier);
    onClose();
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-2xl flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            Upgrade Your Plan
          </DialogTitle>
          <DialogDescription>
            Unlock powerful AI features to enhance your school management
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 md:grid-cols-3 mt-4">
          {(["basic", "pro", "max"] as SubscriptionTier[]).map((tier) => {
            const config = TIER_CONFIG[tier];
            const isCurrentTier = tier === currentTier;
            const isHighlighted = tier === highlightTier;
            
            return (
              <motion.div
                key={tier}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "relative p-4 rounded-xl border-2 transition-all",
                  isHighlighted ? "border-primary shadow-lg scale-105" : "border-border",
                  isCurrentTier && "bg-primary/5"
                )}
              >
                {isHighlighted && (
                  <Badge className="absolute -top-2 left-1/2 -translate-x-1/2 bg-primary">
                    Recommended
                  </Badge>
                )}
                
                <div className="text-center mb-4">
                  <Badge className={getTierColorClasses(tier)}>
                    {tier === "max" && <Crown className="h-3 w-3 mr-1" />}
                    {tier === "pro" && <Zap className="h-3 w-3 mr-1" />}
                    {config.name}
                  </Badge>
                  <p className="text-2xl font-bold mt-2">{config.priceLabel}</p>
                  <p className="text-xs text-muted-foreground">{config.description}</p>
                </div>
                
                <ul className="space-y-2 mb-4">
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-500" />
                    {config.limits.users === -1 ? "Unlimited" : config.limits.users} users
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-emerald-500" />
                    {config.limits.aiQueriesPerDay === -1 ? "Unlimited" : config.limits.aiQueriesPerDay} AI queries/day
                  </li>
                  {config.features.slice(0, 3).map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-emerald-500" />
                      {FEATURE_META[f].name}
                    </li>
                  ))}
                  {config.features.length > 3 && (
                    <li className="text-xs text-muted-foreground">
                      +{config.features.length - 3} more features
                    </li>
                  )}
                </ul>
                
                <Button
                  className="w-full"
                  variant={isCurrentTier ? "outline" : isHighlighted ? "default" : "secondary"}
                  disabled={isCurrentTier}
                  onClick={() => handleUpgrade(tier)}
                >
                  {isCurrentTier ? "Current Plan" : `Choose ${config.name}`}
                </Button>
              </motion.div>
            );
          })}
        </div>
        
        <p className="text-xs text-center text-muted-foreground mt-4">
          Demo mode: Switching plans takes effect immediately
        </p>
      </DialogContent>
    </Dialog>
  );
}

interface TierBadgeProps {
  tier: SubscriptionTier;
  size?: "sm" | "default";
}

export function TierBadge({ tier, size = "default" }: TierBadgeProps) {
  const config = TIER_CONFIG[tier];
  
  return (
    <Badge className={cn(
      getTierColorClasses(tier),
      size === "sm" && "text-[10px] px-1.5 py-0"
    )}>
      {tier === "max" && <Crown className={cn("mr-1", size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3")} />}
      {tier === "pro" && <Zap className={cn("mr-1", size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3")} />}
      {config.name}
    </Badge>
  );
}

export function ProBadge() {
  return (
    <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 text-[10px] px-1.5 py-0">
      <Zap className="h-2.5 w-2.5 mr-0.5" />
      PRO
    </Badge>
  );
}

export function MaxBadge() {
  return (
    <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-[10px] px-1.5 py-0">
      <Crown className="h-2.5 w-2.5 mr-0.5" />
      MAX
    </Badge>
  );
}
