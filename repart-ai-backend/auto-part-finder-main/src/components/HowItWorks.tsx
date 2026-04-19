import { FileText, Phone, CheckCircle } from "lucide-react";

const HowItWorks = () => {
  const steps = [
    {
      icon: FileText,
      number: "1",
      title: "Fill the Form",
      description: "Provide your details and the auto part you need"
    },
    {
      icon: Phone,
      number: "2",
      title: "Get a Call",
      description: "Our AI assistant will call you within 2 minutes"
    },
    {
      icon: CheckCircle,
      number: "3",
      title: "Receive Your Part",
      description: "Get the best price and fast delivery to your location"
    }
  ];

  return (
    <section className="py-16 bg-background">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-foreground">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="text-center relative">
              <div className="inline-flex items-center justify-center w-20 h-20 mb-4 rounded-full bg-primary text-primary-foreground text-2xl font-bold">
                {step.number}
              </div>
              <div className="mb-4">
                <step.icon className="h-12 w-12 mx-auto text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2 text-foreground">
                {step.title}
              </h3>
              <p className="text-muted-foreground">
                {step.description}
              </p>
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-0.5 bg-primary/30" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
