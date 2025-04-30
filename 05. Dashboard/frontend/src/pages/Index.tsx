import { useState, useEffect } from "react";
import { Bot, X } from "lucide-react";
// import { TopBar } from "@/components/dashboard/TopBar";
import KPICards from "@/components/dashboard/KPICards";
import ProbabilityDistribution from "@/components/dashboard/ProbabilityDistribution";
import HeatMap from "@/components/dashboard/HeatMap";
import PriorityClientsTable from "@/components/dashboard/PriorityClientsTable";
import ContactProgress from "@/components/dashboard/ContactProgress";
import AIAssistant from "@/components/dashboard/AIAssistant";
import ExportPanel from "@/components/dashboard/ExportPanel";

const Index = () => {
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Log para depuración
    console.log("Index component mounted");

    // Verificar si la API es accesible
    const checkApi = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || '';
        console.log('Attempting to connect to API:', apiUrl);
        
        if (!apiUrl) {
          setError('No API URL defined in environment variables');
          return;
        }

        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`API responded with status: ${response.status}`);
        }
        console.log('API is accessible');
      } catch (err) {
        console.error('API connection error:', err);
        setError(`Error connecting to API: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    };

    checkApi();
  }, []);

  // Mostrar mensaje de error si existe
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h2 className="text-xl font-bold text-red-600 mb-4">Error de conexión</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <p className="text-gray-600 text-sm">
            Por favor, verifica que el backend esté en funcionamiento y que las variables de entorno estén configuradas correctamente.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      {/* TopBar temporalmente deshabilitada */}
      {/* <TopBar /> */}
      
      <div className="px-2 sm:px-4 py-6 mx-auto" style={{ maxWidth: "1600px" }}>
        <h1 className="text-2xl font-bold mb-6 text-prometeo-black">Dashboard de Ventas</h1>
        
        {/* KPI Cards */}
        <section className="mb-8">
          <KPICards />
        </section>
        
        {/* Main Charts Section */}
        <section className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ProbabilityDistribution />
          <HeatMap />
        </section>
        
        {/* Priority Clients Table */}
        <section className="mb-8">
          <PriorityClientsTable />
        </section>
        
        {/* Contact Progress and Export Section */}
        <section className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ContactProgress />
          <ExportPanel />
        </section>
      </div>
      
      {/* AI Assistant Side Panel */}
      <div 
        className={`fixed top-0 right-0 h-full w-full md:w-96 bg-white shadow-lg transform transition-transform duration-300 z-10 ${
          aiAssistantOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <AIAssistant />
        
        <button
          className="absolute top-1/2 -left-10 transform -translate-y-1/2 bg-prometeo-blue text-white p-2 rounded-l-md shadow-md"
          onClick={() => setAiAssistantOpen(!aiAssistantOpen)}
          aria-label={aiAssistantOpen ? "Cerrar asistente IA" : "Abrir asistente IA"}
        >
          {aiAssistantOpen ? <X size={20} /> : <Bot size={20} />}
        </button>
      </div>
    </div>
  );
};

export default Index;
