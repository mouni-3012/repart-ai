import { Phone } from "lucide-react";

const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full bg-card shadow-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo/Brand */}
          <div className="flex items-center gap-2">
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xl">A</span>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">APEX</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">Auto Parts Excellence</p>
            </div>
          </div>
          
          {/* Contact Info */}
          <div className="flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-lg">
            <Phone className="h-5 w-5 text-primary" />
            <div className="hidden sm:block">
              <p className="text-xs text-muted-foreground">Call Us Now</p>
              <p className="text-sm font-semibold text-foreground">1-800-APEX-AUTO</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
