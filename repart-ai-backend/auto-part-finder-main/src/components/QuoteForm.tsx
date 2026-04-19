import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  User,
  Phone,
  Mail,
  Car,
  Calendar,
  Wrench,
  Hash,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export const QuoteForm = () => {
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    fullName: "",
    phoneNumber: "",
    email: "",
    vehicleMake: "",
    year: "",
    vinNumber: "",
    partNeeded: "",
    additionalNotes: "",
  });

  const [submitting, setSubmitting] = useState(false);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => currentYear - i);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // ✅ REQUIRED FIELD VALIDATION (UPDATED)
    if (!formData.fullName || !formData.phoneNumber || !formData.email) {
      toast({
        title: "Please fill in all required fields",
        description: "Name, Phone, and Email are required",
        variant: "destructive",
      });
      return;
    }

    // ✅ EMAIL VALIDATION (ALWAYS REQUIRED NOW)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast({
        title: "Invalid Email",
        description: "Please enter a valid email address",
        variant: "destructive",
      });
      return;
    }

    // Phone validation
    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
    if (!phoneRegex.test(formData.phoneNumber)) {
      toast({
        title: "Invalid Phone Number",
        description: "Please enter a valid phone number",
        variant: "destructive",
      });
      return;
    }

    try {
      setSubmitting(true);

      const response = await fetch(
        "https://leafed-rihanna-ironically.ngrok-free.dev/submit-form",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            fullName: formData.fullName,
            phoneNumber: formData.phoneNumber,
            email: formData.email,
            vehicleMake: formData.vehicleMake,
            year: formData.year,
            vinNumber: formData.vinNumber,
            partNeeded: formData.partNeeded,
            additionalNotes: formData.additionalNotes,
          }),
        }
      );

      const result = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(result?.message || "Submission failed");
      }

      toast({
        title: "Success!",
        description: "Our AI assistant will call you shortly.",
      });

      // Reset form
      setFormData({
        fullName: "",
        phoneNumber: "",
        email: "",
        vehicleMake: "",
        year: "",
        vinNumber: "",
        partNeeded: "",
        additionalNotes: "",
      });

    } catch (error: any) {
      console.error("Error:", error);

      toast({
        title: "Submission failed",
        description: error.message || "Please try again",
        variant: "destructive",
      });

    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto space-y-6"
    >
      <div className="bg-card rounded-2xl shadow-lg p-8 md:p-10 space-y-6">

        <h2 className="text-2xl font-semibold">
          Contact Information
        </h2>

        {/* Full Name */}
        <div>
          <Label>Full Name *</Label>
          <Input
            placeholder="John Doe"
            value={formData.fullName}
            onChange={(e) =>
              handleInputChange("fullName", e.target.value)
            }
            required
          />
        </div>

        {/* Phone */}
        <div>
          <Label>Phone Number *</Label>
          <Input
            placeholder="+1 555 123 4567"
            value={formData.phoneNumber}
            onChange={(e) =>
              handleInputChange("phoneNumber", e.target.value)
            }
            required
          />
        </div>

        {/* ✅ EMAIL NOW MANDATORY */}
        <div>
          <Label>Email Address *</Label>
          <Input
            type="email"
            placeholder="john@example.com"
            value={formData.email}
            onChange={(e) =>
              handleInputChange("email", e.target.value)
            }
            required
          />
        </div>

        {/* Vehicle */}
        <div>
          <Label>Vehicle (Optional)</Label>
          <Input
            placeholder="Honda Civic"
            value={formData.vehicleMake}
            onChange={(e) =>
              handleInputChange("vehicleMake", e.target.value)
            }
          />
        </div>

        {/* Year */}
        <div>
          <Label>Year</Label>
          <Select
            value={formData.year}
            onValueChange={(value) =>
              handleInputChange("year", value)
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select year" />
            </SelectTrigger>
            <SelectContent>
              {years.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* VIN */}
        <div>
          <Label>VIN (Optional)</Label>
          <Input
            value={formData.vinNumber}
            onChange={(e) =>
              handleInputChange("vinNumber", e.target.value)
            }
          />
        </div>

        {/* Part */}
        <div>
          <Label>Part Needed</Label>
          <Input
            placeholder="Brake pads"
            value={formData.partNeeded}
            onChange={(e) =>
              handleInputChange("partNeeded", e.target.value)
            }
          />
        </div>

        {/* Notes */}
        <div>
          <Label>Additional Notes</Label>
          <Textarea
            value={formData.additionalNotes}
            onChange={(e) =>
              handleInputChange("additionalNotes", e.target.value)
            }
          />
        </div>

        {/* Submit */}
        <Button
          type="submit"
          disabled={submitting}
          className="w-full"
        >
          {submitting ? "Submitting..." : "Submit & Get AI Call"}
        </Button>

      </div>
    </form>
  );
};