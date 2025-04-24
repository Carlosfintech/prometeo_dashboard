import { useState } from "react";
import { Bot, X } from "lucide-react";
import TopBar from "@/components/dashboard/TopBar";
import KPICards from "@/components/dashboard/KPICards";
import ProbabilityDistribution from "@/components/dashboard/ProbabilityDistribution";
import HeatMap from "@/components/dashboard/HeatMap";
import PriorityClientsTable from "@/components/dashboard/PriorityClientsTable";
import ContactProgress from "@/components/dashboard/ContactProgress";
import AIAssistant from "@/components/dashboard/AIAssistant";
import ClientListingFilters from "@/components/dashboard/ExportPanel";

const Index = () => {
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-screen-2xl mx-auto">
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
            
            {/* Contact Progress and Client Listing Section */}
            <section className="mb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ContactProgress />
              <ClientListingFilters />
            </section>
          </div>
        </div>
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
