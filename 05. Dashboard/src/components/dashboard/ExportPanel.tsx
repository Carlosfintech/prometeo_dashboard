import { useState } from 'react';
import { Filter, Download, Search, ChevronDown } from 'lucide-react';

// Definición de tipos para los filtros
interface FilterState {
  age_range: string[];
  income_range: string[];
  risk_profile: string[];
  productos: string[];
  recencia_transaccion: string[];
  monto_promedio_transaccion: string[];
  antiguedad_cliente: string[];
}

// Datos iniciales para los filtros
const initialFilters: FilterState = {
  age_range: [],
  income_range: [],
  risk_profile: [],
  productos: [],
  recencia_transaccion: [],
  monto_promedio_transaccion: [],
  antiguedad_cliente: []
};

// Opciones para cada filtro
const filterOptions = {
  age_range: [
    { value: '18-24', label: '18-24 años' },
    { value: '25-31', label: '25-31 años' },
    { value: '32-38', label: '32-38 años' },
    { value: '39-45', label: '39-45 años' },
    { value: '46-52', label: '46-52 años' },
    { value: '53-59', label: '53-59 años' },
    { value: '60-66', label: '60-66 años' },
    { value: '67-70', label: '67-70 años' }
  ],
  income_range: [
    { value: '30k-50k', label: '$30K - $50K' },
    { value: '50k-100k', label: '$50K - $100K' },
    { value: '100k-150k', label: '$100K - $150K' },
    { value: '150k+', label: 'Más de $150K' }
  ],
  risk_profile: [
    { value: 'conservative', label: 'Conservador' },
    { value: 'moderate', label: 'Moderado' },
    { value: 'aggressive', label: 'Agresivo' }
  ],
  productos: [
    { value: 'checking_account', label: 'Cuenta corriente' },
    { value: 'savings_account', label: 'Cuenta de ahorro' },
    { value: 'credit_card', label: 'Tarjeta de crédito' },
    { value: 'insurance', label: 'Seguro' },
    { value: 'investment', label: 'Inversión' }
  ],
  recencia_transaccion: [
    { value: '0-30', label: 'Últimos 30 días' },
    { value: '31-90', label: '1-3 meses' },
    { value: '91-180', label: '3-6 meses' },
    { value: '180+', label: 'Más de 6 meses' }
  ],
  monto_promedio_transaccion: [
    { value: '0-50', label: '$0 - $50' },
    { value: '51-100', label: '$51 - $100' },
    { value: '101-500', label: '$101 - $500' },
    { value: '500+', label: 'Más de $500' }
  ],
  antiguedad_cliente: [
    { value: '0-180', label: '0-6 meses' },
    { value: '181-365', label: '6-12 meses' },
    { value: '366-730', label: '1-2 años' },
    { value: '730+', label: 'Más de 2 años' }
  ]
};

// Datos de muestra para la tabla
interface Client {
  user_id: string;
  age: number;
  income_range: string;
  risk_profile: string;
  primer_producto: string;
  antiguedad_cliente: number;
  numero_productos: number;
  total_transacciones: number;
  monto_promedio_transaccion: number;
  total_spend: number;
  recencia_transaccion: number;
  probability: number;
}

const sampleClients: Client[] = [
  {
    user_id: 'user_001',
    age: 42,
    income_range: '50k-100k',
    risk_profile: 'moderate',
    primer_producto: 'checking_account',
    antiguedad_cliente: 340,
    numero_productos: 3,
    total_transacciones: 78,
    monto_promedio_transaccion: 125.30,
    total_spend: 9773.40,
    recencia_transaccion: 5,
    probability: 0.76
  },
  {
    user_id: 'user_002',
    age: 35,
    income_range: '30k-50k',
    risk_profile: 'conservative',
    primer_producto: 'savings_account',
    antiguedad_cliente: 156,
    numero_productos: 1,
    total_transacciones: 45,
    monto_promedio_transaccion: 88.75,
    total_spend: 3993.75,
    recencia_transaccion: 12,
    probability: 0.38
  },
  {
    user_id: 'user_003',
    age: 58,
    income_range: '100k-150k',
    risk_profile: 'aggressive',
    primer_producto: 'investment',
    antiguedad_cliente: 583,
    numero_productos: 4,
    total_transacciones: 120,
    monto_promedio_transaccion: 567.42,
    total_spend: 68090.40,
    recencia_transaccion: 2,
    probability: 0.91
  },
  {
    user_id: 'user_004',
    age: 29,
    income_range: '30k-50k',
    risk_profile: 'moderate',
    primer_producto: 'credit_card',
    antiguedad_cliente: 102,
    numero_productos: 2,
    total_transacciones: 63,
    monto_promedio_transaccion: 95.18,
    total_spend: 5996.34,
    recencia_transaccion: 7,
    probability: 0.42
  },
  {
    user_id: 'user_005',
    age: 47,
    income_range: '50k-100k',
    risk_profile: 'conservative',
    primer_producto: 'insurance',
    antiguedad_cliente: 438,
    numero_productos: 2,
    total_transacciones: 53,
    monto_promedio_transaccion: 210.45,
    total_spend: 11153.85,
    recencia_transaccion: 18,
    probability: 0.64
  }
];

export const ClientListingFilters = () => {
  const [filters, setFilters] = useState<FilterState>(initialFilters);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<keyof FilterState | null>(null);
  const [filteredClients, setFilteredClients] = useState<Client[]>(sampleClients);
  
  // Función para actualizar los filtros
  const handleFilterToggle = (filterType: keyof FilterState, value: string) => {
    setFilters(prev => {
      const updatedFilters = { ...prev };
      if (updatedFilters[filterType].includes(value)) {
        updatedFilters[filterType] = updatedFilters[filterType].filter(v => v !== value);
      } else {
        updatedFilters[filterType] = [...updatedFilters[filterType], value];
      }
      return updatedFilters;
    });
  };
  
  // Función para limpiar los filtros
  const clearFilters = () => {
    setFilters(initialFilters);
    setSearchQuery('');
  };
  
  // Función para aplicar los filtros
  const applyFilters = () => {
    // En una implementación real, esto haría una llamada API
    // Por ahora, simulamos el filtrado
    console.log('Filtros aplicados:', filters);
    // Aquí simplemente devolvemos los datos de muestra, pero en un caso real
    // se filtrarían según los criterios seleccionados
    setFilteredClients(sampleClients);
  };
  
  // Total de filtros activos
  const activeFiltersCount = Object.values(filters).flat().length;
  
  // Renderizar un grupo de filtros
  const renderFilterGroup = (filterType: keyof FilterState, title: string) => (
    <div className="relative">
      <button
        className={`px-3 py-1.5 text-sm border ${
          filters[filterType].length > 0 
            ? 'border-prometeo-blue bg-prometeo-blue/10 text-prometeo-blue' 
            : 'border-gray-300 hover:bg-gray-50'
        } rounded-md flex items-center space-x-1`}
        onClick={() => setActiveFilter(activeFilter === filterType ? null : filterType)}
      >
        <span>{title}</span>
        {filters[filterType].length > 0 && (
          <span className="bg-prometeo-blue text-white text-xs rounded-full h-5 w-5 flex items-center justify-center ml-1">
            {filters[filterType].length}
          </span>
        )}
        <ChevronDown size={14} className={activeFilter === filterType ? 'transform rotate-180' : ''} />
      </button>
      
      {/* Dropdown de opciones de filtro */}
      {activeFilter === filterType && (
        <div className="absolute z-10 mt-1 w-56 bg-white border border-gray-200 rounded-md shadow-lg py-1">
          <div className="max-h-60 overflow-y-auto p-2 space-y-1">
            {filterOptions[filterType].map(option => (
              <label 
                key={option.value} 
                className="flex items-center space-x-2 p-1.5 hover:bg-gray-50 rounded"
              >
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-prometeo-blue focus:ring-prometeo-blue"
                  checked={filters[filterType].includes(option.value)}
                  onChange={() => handleFilterToggle(filterType, option.value)}
                />
                <span className="text-sm">{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Listado de Clientes</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {filteredClients.length} clientes
          </span>
          <button 
            className="p-1.5 rounded hover:bg-gray-100 text-gray-600"
            title="Exportar"
          >
            <Download size={16} />
          </button>
        </div>
      </div>
      
      {/* Barra de búsqueda y filtros */}
      <div className="mb-4 space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="flex-1 min-w-[200px] relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={16} className="text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="Buscar cliente..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <div className="flex items-center space-x-1">
            <Filter size={16} className="text-gray-500" />
            <span className="text-sm font-medium">Filtros:</span>
          </div>
          
          {renderFilterGroup('age_range', 'Edad')}
          {renderFilterGroup('income_range', 'Ingresos')}
          {renderFilterGroup('risk_profile', 'Perfil')}
          
          {activeFiltersCount > 0 && (
            <button
              className="px-3 py-1.5 text-sm text-gray-500 hover:text-prometeo-red"
              onClick={clearFilters}
            >
              Limpiar
            </button>
          )}
        </div>
        
        <div className="flex flex-wrap gap-2">
          {renderFilterGroup('productos', 'Productos')}
          {renderFilterGroup('recencia_transaccion', 'Recencia')}
          {renderFilterGroup('monto_promedio_transaccion', 'Monto Prom.')}
          {renderFilterGroup('antiguedad_cliente', 'Antigüedad')}
          
          <button
            className="px-4 py-1.5 text-sm bg-prometeo-blue text-white rounded-md hover:bg-blue-600"
            onClick={applyFilters}
          >
            Aplicar
          </button>
        </div>
      </div>
      
      {/* Tabla de clientes */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3">Cliente</th>
              <th className="px-4 py-3">Edad</th>
              <th className="px-4 py-3">Perfil</th>
              <th className="px-4 py-3">Productos</th>
              <th className="px-4 py-3">Ant. Cliente</th>
              <th className="px-4 py-3">Últ. Trans.</th>
              <th className="px-4 py-3">Monto Prom.</th>
              <th className="px-4 py-3">Prob.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredClients.map((client) => (
              <tr key={client.user_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{client.user_id}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.age}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.risk_profile === 'conservative' && "Conservador"}
                  {client.risk_profile === 'moderate' && "Moderado"}
                  {client.risk_profile === 'aggressive' && "Agresivo"}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.numero_productos}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.antiguedad_cliente} días
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {client.recencia_transaccion} días
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  ${client.monto_promedio_transaccion.toFixed(2)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className={`text-sm font-medium px-2 py-1 rounded-full text-center ${
                    client.probability > 0.7 
                      ? 'bg-prometeo-green bg-opacity-20 text-prometeo-green' 
                      : client.probability > 0.4
                        ? 'bg-prometeo-yellow bg-opacity-20 text-prometeo-yellow'
                        : 'bg-prometeo-red bg-opacity-20 text-prometeo-red'
                  }`}>
                    {(client.probability * 100).toFixed(0)}%
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Paginación */}
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-500">
          Mostrando 1 a {filteredClients.length} de {filteredClients.length} clientes
        </div>
        
        <div className="flex space-x-1">
          <button
            className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-prometeo-gray transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={true}
          >
            Anterior
          </button>
          <button
            className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-prometeo-gray transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={true}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClientListingFilters;
