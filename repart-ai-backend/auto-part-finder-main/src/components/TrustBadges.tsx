import { Shield, Ban, TrendingDown } from "lucide-react";

export const TrustBadges = () => {
  const badges = [
    {
      icon: Shield,
      text: "Secure & Private",
    },
    {
      icon: Ban,
      text: "No Spam",
    },
    {
      icon: TrendingDown,
      text: "Best Price Guarantee",
    },
  ];

  return (
    <div className="flex flex-wrap justify-center items-center gap-6 py-6">
      {badges.map((badge, index) => (
        <div key={index} className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-success" />
          <badge.icon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">{badge.text}</span>
        </div>
      ))}
    </div>
  );
};
