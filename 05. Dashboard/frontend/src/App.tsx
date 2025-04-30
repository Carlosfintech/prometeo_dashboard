import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { useEffect } from "react";
import { api } from "./lib/api";

// Debug component to show environment variables
const DebugInfo = () => (
  <div style={{ position: 'fixed', bottom: 0, right: 0, background: 'black', color: 'white', padding: '5px', zIndex: 9999, maxWidth: '400px', overflow: 'auto' }}>
    <div>API URL: {import.meta.env.VITE_API_URL}</div>
    <div>Modo: {import.meta.env.MODE}</div>
  </div>
);

const App = () => {
  console.log('API URL DEBUG:', import.meta.env.VITE_API_URL);
  
  // Verificar la conexión a la API al cargar
  useEffect(() => {
    // Validar la API al inicio
    const testApiConnection = async () => {
      try {
        console.log('🔍 Probando conexión a la API...');
        const response = await fetch(`${import.meta.env.VITE_API_URL}/metrics/summary`);
        console.log('✅ Respuesta de API (fetch):', response.status, response.statusText);
        
        // También probamos con axios
        api.get('/metrics/summary')
          .then(res => console.log('✅ Respuesta de API (axios):', res.status))
          .catch(err => console.error('❌ Error de API (axios):', err));
      } catch (error) {
        console.error('❌ Error al conectar con la API (fetch):', error);
      }
    };
    
    testApiConnection();
  }, []);
  
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
