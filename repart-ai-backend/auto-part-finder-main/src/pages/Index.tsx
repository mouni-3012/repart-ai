import { QuoteForm } from "@/components/QuoteForm";
import { TrustBadges } from "@/components/TrustBadges";
import BenefitsSection from "@/components/BenefitsSection";
import HowItWorks from "@/components/HowItWorks";
import Header from "@/components/Header";
import { Sparkles } from "lucide-react";
import heroImage from "@/assets/auto-parts-hero.jpg";
import partsSide1 from "@/assets/parts-side-1.jpg";
import partsSide2 from "@/assets/parts-side-2.jpg";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <Header />
      
      {/* Hero Section with Image */}
      <section className="relative w-full h-[400px] md:h-[500px] overflow-hidden">
        <img 
          src={heroImage} 
          alt="Quality Auto Parts" 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background/90" />
        <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
          <div className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-full shadow-lg mb-6">
            <Sparkles className="h-5 w-5" />
            <span className="font-semibold text-sm md:text-base">APEX - AI-Powered Auto Parts</span>
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground text-center mb-4">
            Get Your Personalized Quote from APEX
          </h1>
          <p className="text-lg md:text-xl text-foreground/90 max-w-2xl mx-auto text-center">
            Fill in your details and our APEX AI assistant will call you within 2 minutes
          </p>
        </div>
      </section>

      {/* Benefits Section */}
      <BenefitsSection />

      {/* Form Section with Side Images */}
      <section className="py-16 px-4 bg-muted/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Side Image */}
            <div className="hidden lg:block lg:col-span-3">
              <img 
                src={partsSide1} 
                alt="Engine Parts" 
                className="w-full h-auto rounded-lg shadow-lg sticky top-8"
              />
            </div>

            {/* Form */}
            <div className="lg:col-span-6">
              <div className="text-center mb-8">
                <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
                  Request Your Quote
                </h2>
                <p className="text-lg text-muted-foreground">
                  Complete the form below and we'll get back to you immediately
                </p>
              </div>
              <QuoteForm />
              <TrustBadges />
            </div>

            {/* Right Side Image */}
            <div className="hidden lg:block lg:col-span-3">
              <img 
                src={partsSide2} 
                alt="Auto Filters and Parts" 
                className="w-full h-auto rounded-lg shadow-lg sticky top-8"
              />
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <HowItWorks />

      {/* Additional Info Section */}
      <section className="py-16 bg-primary/5">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            APEX - Quality Auto Parts at Your Fingertips
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            APEX specializes in providing genuine auto parts for all major vehicle brands.
            Our AI-powered system ensures you get the right part at the best price, with 
            personalized service from our expert team. Whether you need brake pads, filters, 
            engine components, or any other spare part, we've got you covered.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm md:text-base">
            <div className="px-6 py-3 bg-card rounded-lg shadow">
              <span className="font-bold text-primary text-2xl block">10,000+</span>
              <span className="text-muted-foreground">Parts Available</span>
            </div>
            <div className="px-6 py-3 bg-card rounded-lg shadow">
              <span className="font-bold text-primary text-2xl block">5,000+</span>
              <span className="text-muted-foreground">Happy Customers</span>
            </div>
            <div className="px-6 py-3 bg-card rounded-lg shadow">
              <span className="font-bold text-primary text-2xl block">24/7</span>
              <span className="text-muted-foreground">Support Available</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Index;
