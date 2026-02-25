import { Navbar } from "@/components/Navbar";
import { HeroSection } from "@/components/HeroSection";
import { UploadSection } from "@/components/UploadSection";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <UploadSection />
    </div>
  );
};

export default Index;
