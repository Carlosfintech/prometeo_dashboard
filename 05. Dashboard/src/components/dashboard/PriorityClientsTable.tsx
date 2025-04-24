import { useState } from 'react';
import { ChevronDown, ChevronUp, Filter, MoreHorizontal, Phone, Calendar, ArrowUpDown, Check, ChevronRight } from 'lucide-react';

// Types for our data
type ClientPriority = 'high' | 'medium' | 'low';

interface Client {
  id: string;
  name: string;
  probability: number;
  status: 'pending' | 'contacted' | 'followup' | 'converted' | 'rejected';
  age: number;
  income: string;
  profile: string;
  products: string[];
  priority: ClientPriority;
}

export const PriorityClientsTable = () => {
  const [clients, setClients] = useState<Client[]>([
    {
      id: 'C-1001',
      name: 'María González',
      probability: 0.87,
      status: 'pending',
      age: 42,
      income: '$3,500',
      profile: 'Conservador',
      products: ['Hogar', 'Auto'],
      priority: 'high'
    },
    {
      id: 'C-1002',
      name: 'José Martínez',
      probability: 0.78,
      status: 'contacted',
      age: 35,
      income: '$2,800',
      profile: 'Moderado',
      products: ['Vida'],
      priority: 'high'
    },
    {
      id: 'C-1003',
      name: 'Carlos Rodríguez',
      probability: 0.71,
      status: 'followup',
      age: 51,
      income: '$4,200',
      profile: 'Agresivo',
      products: ['Inversión', 'Vida', 'Hogar'],
      priority: 'high'
    },
    {
      id: 'C-1004',
      name: 'Ana García',
      probability: 0.65,
      status: 'pending',
      age: 29,
      income: '$2,100',
      profile: 'Moderado',
      products: [],
      priority: 'medium'
    },
    {
      id: 'C-1005',
      name: 'Luisa Hernández',
      probability: 0.59,
      status: 'pending',
      age: 38,
      income: '$3,100',
      profile: 'Conservador',
      products: ['Auto'],
      priority: 'medium'
    },
    {
      id: 'C-1006',
      name: 'Pedro Díaz',
      probability: 0.51,
      status: 'contacted',
      age: 45,
      income: '$3,800',
      profile: 'Conservador',
      products: ['Hogar', 'Salud'],
      priority: 'medium'
    },
    {
      id: 'C-1007',
      name: 'Laura Torres',
      probability: 0.47,
      status: 'pending',
      age: 33,
      income: '$2,500',
      profile: 'Moderado',
      products: ['Vida'],
      priority: 'low'
    },
    {
      id: 'C-1008',
      name: 'Miguel Flores',
      probability: 0.42,
      status: 'followup',
      age: 48,
      income: '$4,000',
      profile: 'Agresivo',
      products: ['Inversión', 'Auto'],
      priority: 'low'
    },
  ]);
  
  const [sortColumn, setSortColumn] = useState<keyof Client>('probability');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [perPage] = useState(5);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  
  // Status options
  const statusOptions: { value: Client['status']; label: string; color: string }[] = [
    { value: 'pending', label: 'Pendiente', color: 'bg-gray-200 text-gray-800' },
    { value: 'contacted', label: 'Contactado', color: 'bg-prometeo-blue bg-opacity-20 text-prometeo-blue' },
    { value: 'followup', label: 'Seguimiento', color: 'bg-prometeo-yellow bg-opacity-20 text-prometeo-yellow' },
    { value: 'converted', label: 'Convertido', color: 'bg-prometeo-green bg-opacity-20 text-prometeo-green' },
    { value: 'rejected', label: 'Rechazado', color: 'bg-prometeo-red bg-opacity-20 text-prometeo-red' }
  ];
  
  // Sort the clients
  const sortedClients = [...clients].sort((a, b) => {
    if (sortColumn === 'probability') {
      return sortDirection === 'asc' ? a.probability - b.probability : b.probability - a.probability;
    } else if (sortColumn === 'age') {
      return sortDirection === 'asc' ? a.age - b.age : b.age - a.age;
    } else {
      const aValue = String(a[sortColumn]);
      const bValue = String(b[sortColumn]);
      return sortDirection === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    }
  });
  
  // Get current page of clients
  const indexOfLast = page * perPage;
  const indexOfFirst = indexOfLast - perPage;
  const currentClients = sortedClients.slice(indexOfFirst, indexOfLast);
  
  // Handle sort
  const handleSort = (column: keyof Client) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };
  
  // Toggle dropdown
  const toggleDropdown = (clientId: string) => {
    setActiveDropdown(activeDropdown === clientId ? null : clientId);
  };
  
  // Handle status change
  const handleStatusChange = (clientId: string, newStatus: Client['status']) => {
    setClients(
      clients.map((client) =>
        client.id === clientId ? { ...client, status: newStatus } : client
      )
    );
    setActiveDropdown(null);
  };
  
  // Function to get status display by value
  const getStatusOption = (status: Client['status']) => {
    return statusOptions.find(option => option.value === status) || statusOptions[0];
  };
  
  // Function to render priority indicator
  const getPriorityIndicator = (priority: ClientPriority) => {
    switch (priority) {
      case 'high':
        return <div className="w-3 h-3 rounded-full bg-prometeo-red"></div>;
      case 'medium':
        return <div className="w-3 h-3 rounded-full bg-prometeo-yellow"></div>;
      case 'low':
        return <div className="w-3 h-3 rounded-full bg-prometeo-green"></div>;
      default:
        return null;
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Clientes Prioritarios</h2>
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-1 px-3 py-1 border border-gray-300 rounded text-sm hover:bg-prometeo-gray transition-colors">
            <Filter size={14} />
            <span>Filtrar</span>
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <div className="flex items-center space-x-1 cursor-pointer" onClick={() => handleSort('name')}>
                  <span>Cliente</span>
                  {sortColumn === 'name' ? (
                    sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="text-gray-400" />
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <div className="flex items-center space-x-1 cursor-pointer" onClick={() => handleSort('probability')}>
                  <span>Prob.</span>
                  {sortColumn === 'probability' ? (
                    sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="text-gray-400" />
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <div className="flex items-center space-x-1 cursor-pointer" onClick={() => handleSort('age')}>
                  <span>Edad</span>
                  {sortColumn === 'age' ? (
                    sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                  ) : (
                    <ArrowUpDown size={14} className="text-gray-400" />
                  )}
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ingresos
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Perfil
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Productos
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {currentClients.map((client) => (
              <tr key={client.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    {getPriorityIndicator(client.priority)}
                    <div className="ml-2">
                      <div className="text-sm font-medium text-gray-900">{client.name}</div>
                      <div className="text-xs text-gray-500">{client.id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {(client.probability * 100).toFixed(0)}%
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="relative">
                    <div 
                      className={`px-2 py-1 rounded-full text-xs ${getStatusOption(client.status).color} flex items-center justify-between w-28 cursor-pointer`}
                      onClick={() => toggleDropdown(client.id)}
                    >
                      <span>{getStatusOption(client.status).label}</span>
                      <ChevronDown size={12} className={`transition-transform ${activeDropdown === client.id ? 'rotate-180' : ''}`} />
                    </div>
                    
                    {activeDropdown === client.id && (
                      <div className="absolute z-10 mt-1 w-40 bg-white border border-gray-200 rounded-md shadow-lg py-1">
                        {statusOptions.map((option) => (
                          <div 
                            key={option.value}
                            className={`flex items-center px-3 py-2 text-sm hover:bg-gray-50 cursor-pointer ${
                              client.status === option.value ? 'bg-gray-50' : ''
                            }`}
                            onClick={() => handleStatusChange(client.id, option.value)}
                          >
                            {client.status === option.value && <Check size={14} className="mr-2 text-prometeo-blue" />}
                            {client.status !== option.value && <div className="w-4 mr-2" />}
                            <span className={`px-2 py-0.5 rounded-full text-xs ${option.color}`}>
                              {option.label}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.age}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.income}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.profile}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex flex-wrap gap-1">
                    {client.products.map((product, idx) => (
                      <span 
                        key={idx} 
                        className="px-1.5 py-0.5 bg-gray-100 text-xs rounded"
                      >
                        {product}
                      </span>
                    ))}
                    {client.products.length === 0 && (
                      <span className="text-xs text-gray-400 italic">Ninguno</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                  <div className="flex justify-end space-x-1">
                    <button 
                      className="p-1.5 rounded hover:bg-prometeo-blue/10 text-gray-600 hover:text-prometeo-blue"
                      title="Contactar"
                      onClick={() => handleStatusChange(client.id, 'contacted')}
                    >
                      <Phone size={16} />
                    </button>
                    <button 
                      className="p-1.5 rounded hover:bg-prometeo-blue/10 text-gray-600 hover:text-prometeo-blue"
                      title="Agendar Seguimiento"
                      onClick={() => handleStatusChange(client.id, 'followup')}
                    >
                      <Calendar size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-500">
          Mostrando {indexOfFirst + 1} a {Math.min(indexOfLast, clients.length)} de {clients.length} clientes
        </div>
        
        <div className="flex space-x-1">
          <button
            className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-prometeo-gray transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Anterior
          </button>
          <button
            className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-prometeo-gray transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={() => setPage(page + 1)}
            disabled={indexOfLast >= clients.length}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
};

export default PriorityClientsTable;
