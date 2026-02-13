import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  icon: LucideIcon;
  index?: number;
}

const StatCard = ({ label, value, change, trend = "neutral", icon: Icon, index = 0 }: StatCardProps) => {
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const card = cardRef.current;
    if (!card) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Calculate distance from center for glow intensity
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
      const maxDistance = Math.sqrt(Math.pow(centerX, 2) + Math.pow(centerY, 2));
      const intensity = 1 - Math.min(distance / maxDistance, 1);
      
      card.style.setProperty('--glow-x', `${x}px`);
      card.style.setProperty('--glow-y', `${y}px`);
      card.style.setProperty('--glow-intensity', intensity.toString());
    };

    const handleMouseLeave = () => {
      card.style.setProperty('--glow-intensity', '0');
    };

    card.addEventListener('mousemove', handleMouseMove);
    card.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      card.removeEventListener('mousemove', handleMouseMove);
      card.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className={cn(
        "relative rounded-xl border border-border bg-card p-5 transition-all duration-300 overflow-hidden",
        "hover:shadow-lg hover:-translate-y-0.5"
      )}
      style={{
        '--glow-x': '50%',
        '--glow-y': '50%',
        '--glow-intensity': '0',
      } as React.CSSProperties}
    >
      {/* Orange glow effect that follows cursor */}
      <div 
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={{
          background: `radial-gradient(
            200px circle at var(--glow-x) var(--glow-y),
            rgba(255, 140, 0, calc(var(--glow-intensity) * 0.15)) 0%,
            rgba(255, 140, 0, calc(var(--glow-intensity) * 0.08)) 30%,
            transparent 70%
          )`,
          opacity: 'var(--glow-intensity)',
        }}
      />
      
      {/* Border glow effect */}
      <div 
        className="pointer-events-none absolute inset-0 rounded-xl transition-opacity duration-300"
        style={{
          background: `radial-gradient(
            250px circle at var(--glow-x) var(--glow-y),
            rgba(255, 140, 0, calc(var(--glow-intensity) * 0.5)) 0%,
            rgba(255, 140, 0, calc(var(--glow-intensity) * 0.2)) 40%,
            transparent 70%
          )`,
          WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
          WebkitMaskComposite: 'xor',
          maskComposite: 'exclude',
          padding: '1px',
          opacity: 'var(--glow-intensity)',
        }}
      />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Icon className="h-4 w-4 text-primary" />
          </div>
          {change && (
            <span className={cn(
              "flex items-center gap-1 text-xs font-medium",
              trend === "up" && "text-success",
              trend === "down" && "text-destructive",
              trend === "neutral" && "text-muted-foreground"
            )}>
              <TrendIcon className="h-3 w-3" />
              {change}
            </span>
          )}
        </div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-muted-foreground mt-1">{label}</p>
      </div>
    </motion.div>
  );
};

export default StatCard;
