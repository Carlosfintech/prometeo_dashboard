import { useState } from 'react';
import { Send, Bot, Lightbulb, Download, Copy, Check, X } from 'lucide-react';

type Message = {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
};

type Suggestion = {
  id: string;
  text: string;
};

export const AIAssistant = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hola, soy tu asistente IA para marketing y ventas de seguros. ¿En qué puedo ayudarte hoy?',
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  // Predefined suggestions
  const suggestions: Suggestion[] = [
    { id: 's1', text: 'Analiza el perfil del cliente C-1003' },
    { id: 's2', text: 'Recomienda productos para clientes con perfil conservador' },
    { id: 's3', text: 'Identifica tendencias en las transacciones de los últimos meses' },
    { id: 's4', text: 'Encuentra clientes con alta probabilidad de contratación' }
  ];
  
  // This is a mock function - would actually call the backend API
  const sendMessage = (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);
    
    // Simulate AI response after delay
    setTimeout(() => {
      let response: string;
      
      // Mock responses based on message content
      if (content.toLowerCase().includes('cliente c-1003')) {
        response = 'Analizando al cliente C-1003 (Carlos Rodríguez):\n\nPerfil: 51 años, ingresos $4,200, perfil agresivo\nProductos: Inversión, Vida, Hogar\nProbabilidad de contratar seguro: 71%\n\nRecomendaciones:\n- Ideal para productos de inversión con mayor riesgo/rendimiento\n- Enfatizar coberturas premium en el seguro de vida\n- Posible interés en ampliar cobertura de hogar con protección de bienes de lujo';
      } else if (content.toLowerCase().includes('perfil conservador')) {
        response = 'Para clientes con perfil conservador, los productos más adecuados son:\n\n1. Seguro de Vida Tradicional: Sin componentes variables, garantía de capital\n2. Seguro de Hogar Integral: Coberturas amplias pero con enfoques tradicionales\n3. Planes de Ahorro Garantizado: Rendimientos fijos sin exposición a mercados\n\nMensajes clave para este perfil:\n- Seguridad y protección a largo plazo\n- Garantías explícitas sobre el capital\n- Estabilidad y respaldo de la aseguradora';
      } else if (content.toLowerCase().includes('tendencias')) {
        response = 'Analizando las tendencias de transacciones recientes:\n\n• Incremento del 23% en compras online respecto al trimestre anterior\n• Mayor gasto en categoría "salud" (+15%) y "hogar" (+18%)\n• Disminución en "viajes" (-12%) y "entretenimiento fuera de casa" (-8%)\n\nEstos patrones sugieren una mayor preocupación por bienestar y seguridad, creando una oportunidad ideal para seguros de salud y protección familiar.';
      } else if (content.toLowerCase().includes('alta probabilidad')) {
        response = 'He identificado 35 clientes con probabilidad >75% de contratación. Las características comunes son:\n\n• Edad: principalmente 40-55 años\n• Perfil de riesgo: moderado (65%)\n• Productos actuales: mínimo 2 productos financieros\n• Transacciones: alta actividad en categorías premium\n\nLos mejores candidatos para contacto inmediato son:\nC-1003, C-1027, C-1042, C-1080, C-1112\n\n¿Deseas que genere una lista completa para exportar?';
      } else {
        response = 'Entiendo tu consulta. Puedo ayudarte analizando datos de clientes, comportamientos de compra, probabilidades de conversión y recomendando estrategias personalizadas. ¿Te gustaría que me enfoque en algún segmento específico de clientes o en alguna estrategia de venta particular?';
      }
      
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        content: response,
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setIsProcessing(false);
    }, 1500);
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      sendMessage(input.trim());
    }
  };
  
  const handleSuggestionClick = (text: string) => {
    if (!isProcessing) {
      sendMessage(text);
    }
  };
  
  const copyToClipboard = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-prometeo-blue rounded-full">
            <Bot size={18} className="text-white" />
          </div>
          <h2 className="text-lg font-bold text-prometeo-black">Asistente IA</h2>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Analiza datos de clientes y ayuda con estrategias de ventas personalizadas
        </p>
      </div>
      
      <div className="flex-1 overflow-auto p-4 space-y-4" style={{ maxHeight: '400px' }}>
        {messages.map((message) => (
          <div 
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[85%] p-3 rounded-lg ${
                message.sender === 'user' 
                  ? 'bg-prometeo-blue/10 text-gray-800' 
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className="whitespace-pre-line text-sm">{message.content}</div>
              
              {message.sender === 'assistant' && (
                <div className="flex justify-end mt-2">
                  <button 
                    className="p-1 hover:bg-gray-100 rounded-full text-gray-500"
                    onClick={() => copyToClipboard(message.id, message.content)}
                    title="Copiar respuesta"
                  >
                    {copiedId === message.id ? (
                      <Check size={14} className="text-prometeo-green" />
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>
                  <button className="p-1 hover:bg-gray-100 rounded-full text-gray-500 ml-1" title="Descargar como PDF">
                    <Download size={14} />
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="max-w-[85%] p-3 bg-white border border-gray-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-prometeo-blue animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-prometeo-blue animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 rounded-full bg-prometeo-blue animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex flex-wrap gap-2 mb-3">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              className="inline-flex items-center px-2.5 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-xs font-medium text-gray-700 transition-colors"
              onClick={() => handleSuggestionClick(suggestion.text)}
              disabled={isProcessing}
            >
              <Lightbulb size={12} className="mr-1 text-prometeo-yellow" />
              {suggestion.text.length > 25 ? suggestion.text.substring(0, 25) + '...' : suggestion.text}
            </button>
          ))}
        </div>
        
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Escribe tu consulta aquí..."
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-prometeo-blue focus:border-transparent"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isProcessing}
          />
          <button
            type="submit"
            className={`p-2 rounded-md ${
              isProcessing || !input.trim() 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-prometeo-blue hover:bg-blue-600 text-white'
            }`}
            disabled={isProcessing || !input.trim()}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIAssistant;
