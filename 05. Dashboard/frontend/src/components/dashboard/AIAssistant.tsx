import { useState } from 'react';
import { Send, Bot, Lightbulb, Download, Copy, Check, AlertCircle } from 'lucide-react';
import axios from 'axios';

type Message = {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  error?: boolean;
};

type Suggestion = {
  id: string;
  text: string;
};

export const AIAssistant = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hola, soy tu asistente IA para consultas sobre clientes. ¿En qué puedo ayudarte hoy?',
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  // Sugerencias enfocadas a consultas sobre clientes
  const suggestions: Suggestion[] = [
    { id: 's1', text: '¿Cuántos clientes tenemos en el segmento Premium?' },
    { id: 's2', text: 'Muéstrame información del cliente con ID 12345' },
    { id: 's3', text: '¿Qué clientes tienen más de 45 años con ingresos altos?' },
    { id: 's4', text: 'Clientes con perfil conservador y alta prioridad' }
  ];
  
  // Función para enviar preguntas al webhook de n8n
  const sendMessage = async (content: string) => {
    // Añadir mensaje del usuario
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);
    
    try {
      // URL del webhook proporcionado - Actualizada a la nueva URL
      const webhookUrl = 'https://carlosfintech.app.n8n.cloud/webhook-test/8327f7f6-124b-4a4f-98e1-49f29a058bb7';
      
      // Enviar la pregunta como parámetro "prompt" usando GET
      const response = await axios.get(webhookUrl, { 
        params: { prompt: content }
      });
      
      // Imprimir la respuesta completa para depurar
      console.log('Respuesta completa del webhook:', response.data);
      
      // Obtener la respuesta del webhook - Manejar múltiples formatos posibles
      let assistantResponse = '';
      
      if (response.data && typeof response.data === 'object') {
        // Caso 1: { respuesta: "texto" } - formato esperado
        if (response.data.respuesta) {
          assistantResponse = response.data.respuesta;
        }
        // Caso 2: { output: "texto" } - posible formato alternativo
        else if (response.data.output) {
          assistantResponse = response.data.output;
        }
        // Caso 3: { data: "texto" } - otro posible formato
        else if (response.data.data) {
          assistantResponse = response.data.data;
        }
        // Caso 4: La respuesta es la propiedad que tenga un string más largo
        else {
          const textProps = Object.entries(response.data)
            .filter(([_key, value]) => typeof value === 'string' && value.length > 10)
            .sort(([_k1, a], [_k2, b]) => (b as string).length - (a as string).length);
          
          if (textProps.length > 0) {
            assistantResponse = textProps[0][1] as string;
          }
        }
      } 
      // Caso 5: La respuesta es directamente un string
      else if (typeof response.data === 'string') {
        assistantResponse = response.data;
      }
      
      // Si no logramos extraer una respuesta
      if (!assistantResponse) {
        assistantResponse = 'No pude obtener la información solicitada. Por favor, intenta con otra pregunta. (Formato de respuesta incorrecto)';
      }
      
      // Añadir mensaje del asistente con la respuesta
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        content: assistantResponse,
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error al consultar el webhook:', error);
      
      // Mensaje de error si falla la conexión
      const errorMessage: Message = {
        id: `assistant-error-${Date.now()}`,
        content: 'Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, inténtalo de nuevo más tarde.',
        sender: 'assistant',
        timestamp: new Date(),
        error: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
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
          <h2 className="text-lg font-bold text-prometeo-black">Asistente IA para Consultas</h2>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Consulta información sobre tus clientes conectando directamente con la base de datos
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
                  : message.error
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-white border border-gray-200'
              }`}
            >
              {message.error && (
                <div className="flex items-center text-red-500 mb-2">
                  <AlertCircle size={14} className="mr-1" />
                  <span className="text-xs font-medium">Error</span>
                </div>
              )}
              
              <div className="whitespace-pre-line text-sm">{message.content}</div>
              
              {message.sender === 'assistant' && !message.error && (
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
            placeholder="Pregunta sobre tus clientes..."
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
