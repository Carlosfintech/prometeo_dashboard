import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

// Debug component to show environment variables
const DebugInfo = () => (
  <div style={{ position: 'fixed', bottom: 0, right: 0, background: 'black', color: 'white', padding: '5px', zIndex: 9999 }}>
    API URL: {import.meta.env.VITE_API_URL}
  </div>
);

const App = () => {
  console.log('API URL DEBUG:', import.meta.env.VITE_API_URL);
  return (
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <DebugInfo />
    </TooltipProvider>
  );
};

export default App;
