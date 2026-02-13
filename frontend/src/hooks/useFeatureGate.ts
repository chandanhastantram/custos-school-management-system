import { useSubscriptionStore, AIFeature, FEATURE_META, TIER_CONFIG, SubscriptionTier } from "@/store/subscription-store";

interface FeatureGateResult {
  allowed: boolean;
  currentTier: SubscriptionTier;
  requiredTier: SubscriptionTier;
  featureName: string;
  upgradeMessage: string;
}

/**
 * Hook to check if a feature is available for the current subscription tier
 */
export function useFeatureGate(feature: AIFeature): FeatureGateResult {
  const { tier, hasFeature } = useSubscriptionStore();
  const allowed = hasFeature(feature);
  const meta = FEATURE_META[feature];
  
  return {
    allowed,
    currentTier: tier,
    requiredTier: meta.minTier,
    featureName: meta.name,
    upgradeMessage: allowed 
      ? "" 
      : `Upgrade to ${TIER_CONFIG[meta.minTier].name} to unlock ${meta.name}`,
  };
}

/**
 * Hook to check AI query availability
 */
export function useAIQueryLimit() {
  const { 
    tier, 
    aiQueriesUsedToday, 
    incrementAIQuery, 
    getQueryLimit, 
    getRemainingQueries 
  } = useSubscriptionStore();
  
  const limit = getQueryLimit();
  const remaining = getRemainingQueries();
  const isUnlimited = limit === -1;
  
  return {
    tier,
    queriesUsed: aiQueriesUsedToday,
    queryLimit: limit,
    remaining,
    isUnlimited,
    canQuery: isUnlimited || remaining > 0,
    useQuery: incrementAIQuery,
    usageText: isUnlimited 
      ? "Unlimited queries" 
      : `${remaining}/${limit} queries remaining today`,
  };
}

/**
 * Get all features with their availability status
 */
export function useAllFeatures() {
  const { tier, hasFeature } = useSubscriptionStore();
  
  return Object.entries(FEATURE_META).map(([key, meta]) => ({
    id: key as AIFeature,
    ...meta,
    available: hasFeature(key as AIFeature),
    currentTier: tier,
  }));
}
