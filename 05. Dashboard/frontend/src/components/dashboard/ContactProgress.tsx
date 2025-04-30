import { useState, useEffect } from 'react';
import { Target, ArrowRight, Calendar, AlertTriangle, Check, Edit2, Save, RefreshCw } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';

// Tipado para la respuesta del API
interface ContactProgressData {
  total_contacted: number;
  total_prioritized: number;
  monthly_target: number;
  contacted_this_month: number;
  days_remaining: number;
  daily_needed: number;
  daily_expected: number;
  difference: number;
  remaining_contacts: number;
  projection_message: string;
}

interface ProgressBarProps {
  value: number;
  total: number;
  label?: string;
  color?: string;
  showPercentage?: boolean;
  height?: string;
}

const ProgressBar = ({ 
  value, 
  total, 
  label, 
  color = 'bg-prometeo-blue', 
  showPercentage = true,
  height = 'h-4'
}: ProgressBarProps) => {
  // Asegurar que el valor no exceda el total y que no sea negativo
  const safeValue = Math.min(Math.max(0, value), total);
  // Evitar división por cero
  const percentage = total > 0 ? Math.round((safeValue / total) * 100) : 0;
  
  return (
    <div className="w-full">
      {label && <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        {showPercentage && <span>{percentage}%</span>}
      </div>}
      <div className={`w-full bg-gray-200 rounded-full ${height}`}>
        <div 
          className={`${color} rounded-full ${height}`} 
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export const ContactProgress = () => {
  const queryClient = useQueryClient();
  // Estado local para la meta mensual y modo de edición
  const [isEditingTarget, setIsEditingTarget] = useState(false);
  const [tempTarget, setTempTarget] = useState('');
  
  // Obtener datos de progreso desde el API
  const { 
    data: progressData, 
    isLoading, 
    isError, 
    refetch 
  } = useQuery<ContactProgressData>({
    queryKey: ['contactProgress'],
    queryFn: () => api.get('/contacts/progress').then(res => res.data),
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    refetchInterval: 5000,
  });
  
  // --- Mutation for updating monthly target --- 
  const updateTargetMutation = useMutation({
    mutationFn: (newTarget: number) => 
      api.put('/contacts/config', { monthly_target: newTarget }),
    onSuccess: () => {
      // When mutation is successful, invalidate the contacts progress query to refetch data
      queryClient.invalidateQueries({ queryKey: ['contactProgress'] });
      console.log("Monthly target updated successfully, refetching progress...");
    },
    onError: (error) => {
      console.error("Error updating monthly target:", error);
      // Optionally: show an error message to the user
      // Revert tempTarget if needed
      if (progressData) {
        setTempTarget(progressData.monthly_target.toString());
      }
    },
  });
  
  // Initialize tempTarget when data loads or editing starts
  useEffect(() => {
    if (progressData && !isEditingTarget) {
      setTempTarget(progressData.monthly_target.toString());
    } else if (progressData && isEditingTarget && tempTarget === '') {
      // Ensure input is populated when edit mode starts
      setTempTarget(progressData.monthly_target.toString());
    }
  }, [progressData, isEditingTarget]); // Rerun when data loads or edit mode changes
  
  // Manejar la actualización de la meta mensual (aquí se invocaría al API en un caso real)
  const handleSaveTarget = () => {
    const newTarget = parseInt(tempTarget, 10);
    if (!isNaN(newTarget) && newTarget > 0) {
      updateTargetMutation.mutate(newTarget); // Trigger the mutation
    } else {
      // Invalid input, revert tempTarget
      if (progressData) {
        setTempTarget(progressData.monthly_target.toString());
      }
    }
    setIsEditingTarget(false); // Exit editing mode regardless of success/error (handled by onError)
  };
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!progressData) return;
    if (e.key === 'Enter') {
      handleSaveTarget();
    } else if (e.key === 'Escape') {
      setTempTarget(progressData.monthly_target.toString());
      setIsEditingTarget(false);
    }
  };
  
  const handleEditClick = () => {
    if (progressData) {
      setTempTarget(progressData.monthly_target.toString()); // Ensure input has current value
      setIsEditingTarget(true);
    }
  };
  
  // Si está cargando, mostrar skeleton
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Progreso de Contactos</h2>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded-full"></div>
          <div className="h-6 bg-gray-200 rounded"></div>
          <div className="h-8 bg-gray-200 rounded-full"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }
  
  // Si hay error o no hay datos, mostrar mensaje de error
  if (isError || !progressData) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Progreso de Contactos</h2>
        </div>
        <div className="flex flex-col items-center justify-center h-64 text-red-500">
          <AlertTriangle size={32} className="mb-2" />
          <p className="text-center mb-4">Error al cargar los datos de progreso de contactos</p>
          <button 
            onClick={() => refetch()} 
            className="flex items-center gap-2 px-4 py-2 bg-prometeo-blue text-white rounded-md hover:bg-prometeo-blue-dark"
          >
            <RefreshCw size={16} />
            <span>Reintentar</span>
          </button>
        </div>
      </div>
    );
  }
  
  // Calculate progress percentage for general progress
  const generalProgressPercentage = progressData.total_prioritized > 0 
    ? Math.round((progressData.total_contacted / progressData.total_prioritized) * 100) 
    : 0;
  
  // Calcular progreso mensual
  const monthlyProgressPercentage = progressData.monthly_target > 0 
    ? Math.round((progressData.contacted_this_month / progressData.monthly_target) * 100) 
    : 0;
  
  // Determinar color de estado basado en el porcentaje
  const getStatusColor = (percentage: number) => {
    if (percentage < 33) return 'text-prometeo-red';
    if (percentage < 66) return 'text-prometeo-yellow';
    return 'text-prometeo-green';
  };
  
  // Calcular porcentaje proyectado (limitado a 100% para la visualización)
  const projectedContacts = progressData.contacted_this_month + (progressData.daily_expected * progressData.days_remaining);
  const projectedPercentage = Math.min(
    Math.round((projectedContacts / progressData.monthly_target) * 100),
    100
  );
  
  // Determinar si se alcanzará la meta
  const willReachTarget = projectedContacts >= progressData.monthly_target;
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Progreso de Contactos</h2>
        <button 
          className="text-gray-500 hover:text-prometeo-blue transition-colors"
          onClick={() => refetch()}
          title="Actualizar datos (Manual)"
        >
          <RefreshCw size={16} />
        </button>
      </div>
      
      <div className="mb-6">
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-sm font-medium">
            Progreso General (vs Potenciales)
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold ${getStatusColor(generalProgressPercentage)}`}>
              {generalProgressPercentage}%
            </span>
            <span className="text-xs text-gray-500">
               Total: {progressData.total_prioritized}
            </span>
          </div>
        </div>
        <ProgressBar 
          value={progressData.total_contacted} 
          total={progressData.total_prioritized} 
          color="bg-prometeo-blue" 
          height="h-6"
        />
        <div className="flex justify-start text-xs text-gray-500 mt-1">
          <span>{progressData.total_contacted} de {progressData.total_prioritized} clientes contactados</span>
        </div>
      </div>
      
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium">Meta Mensual</h3>
          <div className="flex items-center gap-2">
            {isEditingTarget ? (
              <div className="flex items-center">
                <input 
                  type="number" 
                  className="w-20 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-prometeo-blue"
                  value={tempTarget}
                  onChange={(e) => setTempTarget(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onBlur={handleSaveTarget}
                  autoFocus
                  min="1"
                />
                <button 
                  className={`ml-1 p-1 rounded ${updateTargetMutation.isPending ? 'text-gray-400' : 'text-prometeo-green hover:bg-gray-100'}`}
                  onClick={handleSaveTarget}
                  title="Guardar meta"
                  disabled={updateTargetMutation.isPending}
                >
                  <Save size={14} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Target size={14} />
                <span>{progressData.monthly_target} contactos</span>
                <button 
                  className="ml-1 p-1 text-gray-400 hover:text-prometeo-blue hover:bg-gray-100 rounded"
                  onClick={handleEditClick}
                  title="Editar meta"
                >
                  <Edit2 size={12} />
                </button>
              </div>
            )}
          </div>
        </div>
        
        <ProgressBar 
          value={progressData.contacted_this_month} 
          total={progressData.monthly_target} 
          color="bg-prometeo-blue" 
          label={`Progreso hacia la meta (${monthlyProgressPercentage}%)`}
        />
        
        <div className="mt-4 p-4 bg-gray-50 rounded-md border border-gray-200">
          <div className="flex items-center mb-3">
            <Calendar size={16} className="text-prometeo-blue mr-2 flex-shrink-0" />
            <span className="text-sm font-medium">Faltan {progressData.days_remaining} días para fin de mes</span>
          </div>
          
          <div className="grid grid-cols-1 gap-3">
            <div className="flex justify-between items-center p-2 bg-white rounded border border-gray-100">
              <span className="text-sm text-gray-600">Ritmo necesario:</span>
              <div className="flex items-center">
                <span className="text-sm font-bold">{progressData.daily_needed} contactos/día</span>
              </div>
            </div>
            
            <div className="flex justify-between items-center p-2 bg-white rounded border border-gray-100">
              <span className="text-sm text-gray-600">Ritmo actual:</span>
              <div className="flex items-center">
                <span className="text-sm">{progressData.daily_expected} contactos/día</span>
              </div>
            </div>
            
            <div className="flex justify-between items-center p-2 bg-white rounded border border-gray-100">
              <span className="text-sm text-gray-600">Contactos Pendientes (Meta):</span>
              <div className="flex items-center">
                <span className={`text-sm font-semibold ${progressData.remaining_contacts === 0 ? 'text-prometeo-green' : 'text-gray-700'}`}>
                  {progressData.remaining_contacts} contactos
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium">Proyección de Cumplimiento</h3>
          <div className="text-xs text-gray-500">
            A ritmo actual ({progressData.daily_expected} contactos/día)
          </div>
        </div>
        
        <ProgressBar 
          value={projectedContacts} 
          total={progressData.monthly_target} 
          color={willReachTarget ? "bg-prometeo-green" : "bg-prometeo-yellow"} 
          showPercentage={true}
        />
        
        <div className="mt-3 p-2 rounded-md bg-gray-50 border border-gray-200">
          <div className="flex items-center">
            {willReachTarget 
              ? <Check size={16} className="text-prometeo-green mr-2 flex-shrink-0" /> 
              : <AlertTriangle size={16} className="text-prometeo-yellow mr-2 flex-shrink-0" />
            }
            <span className="text-sm text-gray-700">
              {progressData.projection_message}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactProgress;
