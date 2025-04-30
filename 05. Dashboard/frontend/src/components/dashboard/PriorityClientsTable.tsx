import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, ChevronUp, Filter, MoreHorizontal, Phone, Calendar, Eye, Check, ArrowUpDown } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api } from '../../lib/api';
import axios from 'axios';

// Types for our data
type ClientPriority = 'high' | 'medium' | 'low';
type ClientStatus = 'pending' | 'contacted' | 'followup' | 'converted' | 'rejected';

interface Client {
  id: number;
  user_id: string;
  probability: number;
  status: ClientStatus;
  age?: number;
  income_range?: string;
  risk_profile?: string;
  products?: string[];
  priority?: ClientPriority;
}

export const PriorityClientsTable = () => {
  const [sortColumn, setSortColumn] = useState<keyof Client>('probability');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [perPage] = useState(5);
  const [openActionMenu, setOpenActionMenu] = useState<number | null>(null);
  const [menuCoords, setMenuCoords] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  
  // Acceso al queryClient para invalidar queries después de mutaciones
  const queryClient = useQueryClient();
  
  // Efecto para cerrar el menú cuando se hace clic fuera
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (openActionMenu !== null) {
        const target = e.target as HTMLElement;
        if (!target.closest('.status-dropdown-container') && !target.closest('.status-menu-container')) {
          setOpenActionMenu(null);
        }
      }
    };
    
    // Agregar listener
    document.addEventListener('mousedown', handleClickOutside);
    
    // Limpiar listener
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openActionMenu]);
  
  // Obtener la lista de clientes prioritarios
  const { data, isLoading, error } = useQuery({
    queryKey: ["priorityList", page, perPage],
    queryFn: async () => {
      const response = await api.get(`/clients/priority-list?page=${page}&size=${perPage}`);
      return response.data;
    },
    placeholderData: (previousData) => previousData,
    refetchOnWindowFocus: false,
    staleTime: 0, // Considerar los datos obsoletos inmediatamente
    gcTime: 5 * 60 * 1000, // 5 minutos en caché (reemplaza cacheTime en v5)
    retry: 1, // Reintentar una vez en caso de error
  });
  
  // Actualizar el estado de un cliente
  const updateStatusMutation = useMutation({
    mutationFn: (data: { clientId: number; status: ClientStatus }) => 
      axios.patch(`${import.meta.env.VITE_API_URL}/clients/${data.clientId}/status`, { status: data.status }),
    onSuccess: () => {
      // Invalidar consultas para forzar recarga de datos
      queryClient.invalidateQueries({ queryKey: ['priorityList'] });
      queryClient.invalidateQueries({ queryKey: ['metricsSummary'] });
      // Invalidar distribución de probabilidades para actualizar el gráfico
      queryClient.invalidateQueries({ queryKey: ['probDist'] });
      // Invalidar progreso de contactos para actualización en tiempo real
      queryClient.invalidateQueries({ queryKey: ['contactProgress'] });
    },
  });
  
  // Manejar el cambio de estado
  const handleStatusChange = (clientId: number, status: ClientStatus) => {
    // Optimistic update - actualizar la UI inmediatamente
    const previousData = queryClient.getQueryData<Client[]>(["priorityList", page, perPage]);
    
    if (previousData) {
      queryClient.setQueryData(["priorityList", page, perPage], 
        previousData.map(client => 
          client.id === clientId 
            ? { ...client, status } 
            : client
        )
      );
    }
    
    updateStatusMutation.mutate(
      { clientId, status },
      {
        onSuccess: () => {
          setOpenActionMenu(null); // Cerrar menú después de actualizar
          
          // Reforzar que se recarguen los datos
          queryClient.invalidateQueries({ queryKey: ['priorityList'] });
          // También actualizar contactProgress para actualización en tiempo real
          queryClient.invalidateQueries({ queryKey: ['contactProgress'] });
          // También actualizar KPI cards en tiempo real
          queryClient.invalidateQueries({ queryKey: ['metricsSummary'] });
          // Actualizar distribución de probabilidad en tiempo real si aplica
          queryClient.invalidateQueries({ queryKey: ['probDist'] });
          
          // Mostrar toast según el estado
          let message = '';
          let icon = '';
          
          switch(status) {
            case 'contacted':
              message = 'Cliente marcado como contactado';
              icon = '✓';
              break;
            case 'followup':
              message = 'Cliente en seguimiento';
              icon = '👁️';
              break;
            case 'converted':
              message = '¡Cliente convertido exitosamente!';
              icon = '🎉';
              break;
            case 'rejected':
              message = 'Cliente rechazado';
              icon = '✗';
              break;
            default:
              message = 'Estado del cliente actualizado';
              icon = '✓';
          }
          
          toast.success(`${icon} ${message}`, {
            position: 'bottom-right',
            duration: 3000,
          });
        },
        onError: (error) => {
          console.error("Error al actualizar estado:", error);
          
          // Restaurar datos anteriores si hubo error (rollback)
          if (previousData) {
            queryClient.setQueryData(["priorityList", page, perPage], previousData);
          }
          
          toast.error('Error al actualizar el estado del cliente', {
            position: 'bottom-right',
            duration: 3000,
          });
        }
      }
    );
  };
  
  // Toggle para el menú de acciones
  const toggleActionMenu = (event: React.MouseEvent, clientId: number) => {
    event.stopPropagation();
    if (openActionMenu === clientId) {
      setOpenActionMenu(null);
      return;
    }
    const btn = event.currentTarget as HTMLElement;
    const rect = btn.getBoundingClientRect();
    setMenuCoords({ x: rect.left, y: rect.bottom });
    setOpenActionMenu(clientId);
  };
  
  // Si está cargando, mostrar un indicador de carga
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Clientes Prioritarios</h2>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded"></div>
          {[...Array(5)].map((_, index) => (
            <div key={index} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }
  
  // Si hay un error, mostrar un mensaje
  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Clientes Prioritarios</h2>
        </div>
        <div className="text-prometeo-red">
          Error al cargar los datos. Por favor, intenta de nuevo más tarde.
        </div>
      </div>
    );
  }
  
  // Sort the clients
  const clientsData = data as Client[] || [];
  const sortedClients = [...clientsData].sort((a, b) => {
    if (sortColumn === 'probability') {
      return sortDirection === 'asc' ? a.probability - b.probability : b.probability - a.probability;
    } else if (sortColumn === 'age' && a.age !== undefined && b.age !== undefined) {
      return sortDirection === 'asc' ? a.age - b.age : b.age - a.age;
    } else {
      const aValue = String(a[sortColumn] || '');
      const bValue = String(b[sortColumn] || '');
      return sortDirection === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    }
  });
  
  // Handle sort
  const handleSort = (column: keyof Client) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };
  
  // Obtener etiqueta basada en el estado
  const getStatusLabel = (status: string): string => {
    const statusMap: Record<string, string> = {
      pending: 'Pendiente',
      contacted: 'Contactado',
      followup: 'Seguimiento',
      converted: 'Convertido',
      rejected: 'Rechazado'
    };
    return statusMap[status] || status;
  };
  
  // Function to render priority indicator
  const getPriorityIndicator = (priority?: ClientPriority) => {
    switch (priority) {
      case 'high':
        return <div className="w-3 h-3 rounded-full bg-prometeo-red"></div>;
      case 'medium':
        return <div className="w-3 h-3 rounded-full bg-prometeo-yellow"></div>;
      case 'low':
        return <div className="w-3 h-3 rounded-full bg-prometeo-green"></div>;
      default:
        return <div className="w-3 h-3 rounded-full bg-gray-300"></div>;
    }
  };
  
  // Obtener clase de color según el estado
  const getStatusColorClass = (status: ClientStatus): string => {
    switch(status) {
      case 'pending':
        return 'bg-gray-200 text-gray-800';
      case 'contacted':
        return 'bg-prometeo-blue bg-opacity-20 text-prometeo-blue';
      case 'followup':
        return 'bg-prometeo-yellow bg-opacity-20 text-prometeo-yellow';
      case 'converted':
        return 'bg-prometeo-green bg-opacity-20 text-prometeo-green';
      case 'rejected':
        return 'bg-prometeo-red bg-opacity-20 text-prometeo-red';
      default:
        return 'bg-gray-200 text-gray-800';
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
      
      <div className="overflow-x-auto overflow-y-visible relative">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <div className="flex items-center space-x-1 cursor-pointer" onClick={() => handleSort('user_id')}>
                  <span>Cliente</span>
                  {sortColumn === 'user_id' ? (
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
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedClients.map((client) => (
              <tr key={client.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="ml-1 mr-3">
                    {getPriorityIndicator(client.priority)}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-prometeo-black">{client.user_id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm">{(client.probability * 100).toFixed(1)}%</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="relative inline-block status-menu-container overflow-visible">
                    <button
                      className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${getStatusColorClass(client.status)}`}
                      onClick={(e) => toggleActionMenu(e, client.id)}
                    >
                      {getStatusLabel(client.status)}
                      <ChevronDown size={12} className="ml-1" />
                    </button>
                    {openActionMenu === client.id && (
                      <div className="absolute left-0 top-full mt-1 w-40 bg-white shadow-lg border border-gray-200 rounded-md z-50">
                        <div className="py-1">
                          <button
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${client.status === 'pending' ? 'bg-gray-100 text-gray-800 font-medium' : 'text-gray-700'}`}
                            onClick={() => handleStatusChange(client.id, 'pending')}
                          >
                            Pendiente
                            {client.status === 'pending' && <Check size={14} className="inline ml-2" />}
                          </button>
                          <button
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${client.status === 'contacted' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'}`}
                            onClick={() => handleStatusChange(client.id, 'contacted')}
                          >
                            Contactado
                            {client.status === 'contacted' && <Check size={14} className="inline ml-2" />}
                          </button>
                          <button
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${client.status === 'followup' ? 'bg-yellow-50 text-yellow-600 font-medium' : 'text-gray-700'}`}
                            onClick={() => handleStatusChange(client.id, 'followup')}
                          >
                            Seguimiento
                            {client.status === 'followup' && <Check size={14} className="inline ml-2" />}
                          </button>
                          <button
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${client.status === 'converted' ? 'bg-green-50 text-green-600 font-medium' : 'text-gray-700'}`}
                            onClick={() => handleStatusChange(client.id, 'converted')}
                          >
                            Convertido
                            {client.status === 'converted' && <Check size={14} className="inline ml-2" />}
                          </button>
                          <button
                            className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${client.status === 'rejected' ? 'bg-red-50 text-red-600 font-medium' : 'text-gray-700'}`}
                            onClick={() => handleStatusChange(client.id, 'rejected')}
                          >
                            Rechazado
                            {client.status === 'rejected' && <Check size={14} className="inline ml-2" />}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm">{client.age || '-'}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm">{client.income_range || '-'}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm">{client.risk_profile || '-'}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button 
                    className="inline-flex items-center rounded-full p-1.5 bg-prometeo-blue/10 text-prometeo-blue hover:bg-prometeo-blue/20"
                      title="Contactar"
                    >
                    <Phone size={14} />
                    </button>
                    <button 
                    className="inline-flex items-center rounded-full p-1.5 bg-prometeo-green/10 text-prometeo-green hover:bg-prometeo-green/20"
                    title="Agendar"
                    >
                    <Calendar size={14} />
                    </button>
                    <button 
                    className="inline-flex items-center rounded-full p-1.5 bg-prometeo-gray/10 text-prometeo-black hover:bg-prometeo-gray/20"
                    title="Ver detalle"
                  >
                    <Eye size={14} />
                    </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Paginación */}
      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-500">
          Mostrando {sortedClients.length} de {clientsData.length} clientes
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className={`px-3 py-1 rounded text-sm ${
              page === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-prometeo-gray/10 text-prometeo-black hover:bg-prometeo-gray/20'
            }`}
          >
            Anterior
          </button>
          <button
            onClick={() => setPage(page + 1)}
            disabled={!data || clientsData.length < perPage}
            className={`px-3 py-1 rounded text-sm ${
              !data || clientsData.length < perPage
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-prometeo-gray/10 text-prometeo-black hover:bg-prometeo-gray/20'
            }`}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
};

export default PriorityClientsTable;
