import { Shield, Clock, ThumbsUp, Headphones } from "lucide-react";

const BenefitsSection = () => {
  const benefits = [
    {
      icon: Clock,
      title: "Quick Response",
      description: "Our AI assistant calls you back within 2 minutes"
    },
    {
      icon: ThumbsUp,
      title: "Best Prices",
      description: "Competitive pricing on all genuine auto parts"
    },
    {
      icon: Shield,
      title: "Quality Guaranteed",
      description: "100% authentic parts with warranty coverage"
    },
    {
      icon: Headphones,
      title: "Expert Support",
      description: "Professional assistance from auto parts specialists"
    }
  ];

  return (
    <section className="py-16 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-foreground">
          Why Choose APEX Auto Parts?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {benefits.map((benefit, index) => (
            <div 
              key={index}
              className="text-center p-6 bg-card rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 mb-4 rounded-full bg-primary/10">
                <benefit.icon className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-foreground">
                {benefit.title}
              </h3>
              <p className="text-muted-foreground">
                {benefit.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BenefitsSection;
