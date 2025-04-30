import { useState, useEffect } from 'react';
import { Info, RefreshCw, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';

// Tipos para los datos del mapa de calor
interface HeatMapData {
  x_categories: string[];
  y_categories: string[];
  values: number[][];
}

interface HeatMapVariable {
  value: string;
  label: string;
}

interface HeatMapVariables {
  variables: string[];
  categories: Record<string, string[]>;
}

export const HeatMap = () => {
  // Estado para la selección de ejes y métrica
  const [xAxis, setXAxis] = useState('age');
  const [yAxis, setYAxis] = useState('income_range');
  const [metric, setMetric] = useState<'probability' | 'count'>('probability');
  const [hoveredCell, setHoveredCell] = useState<{ x: number; y: number; value: number } | null>(null);
  
  // Variables disponibles para los ejes (se cargarán desde la API)
  const { data: variablesData, isLoading: isLoadingVariables } = useQuery<HeatMapVariables>({
    queryKey: ['heatmapVariables'],
    queryFn: () => api.get('/metrics/heatmap/variables').then(res => res.data),
  });
  
  // Cargar datos del mapa de calor
  const { data, isLoading, error, refetch } = useQuery<HeatMapData>({
    queryKey: ['heatmap', xAxis, yAxis, metric],
    queryFn: () => api.get('/metrics/heatmap', { 
      params: { x: xAxis, y: yAxis, metric } 
    }).then(res => res.data),
    refetchOnWindowFocus: false,
  });
  
  // Variable mapping para mostrar nombres amigables
  const variableLabels: Record<string, string> = {
    age: 'Edad',
    income_range: 'Rango de Ingresos',
    risk_profile: 'Perfil de Riesgo',
    status: 'Estado de Contacto',
  };
  
  // Lista de variables disponibles para los selectores (excluyendo 'priority')
  const availableVariables = variablesData?.variables
    .filter(v => v !== 'priority')
    .map(v => ({ value: v, label: variableLabels[v] || v })) || [];
  
  // Función para obtener color basado en el valor (probabilidad)
  const getBackgroundColor = (value: number) => {
    // Escala de azules
    if (value < 0.2) return 'bg-blue-100';
    if (value < 0.3) return 'bg-blue-200';
    if (value < 0.4) return 'bg-blue-300';
    if (value < 0.5) return 'bg-blue-400';
    return 'bg-blue-500';
  };
  
  // Obtener color de texto basado en el fondo
  const getTextColor = (value: number) => {
    return value >= 0.4 ? 'text-white' : 'text-gray-700';
  };
  
  // Formatear valores para mostrar en las celdas
  const formatCellValue = (value: number, metricType: 'probability' | 'count'): string => {
    if (metricType === 'probability') {
      return `${(value * 100).toFixed(0)}%`;
    } else {
      return value.toLocaleString(); // Formatear números con separadores de miles
    }
  };
  
  // Calcular la oportunidad financiera para el tooltip
  const calculateFinancialOpportunity = (value: number, count: number) => {
    if (metric !== 'probability') return null;
    
    const potentialClients = count;
    const expectedConversion = Math.round(potentialClients * 0.2); // 20% de conversión
    const financial = expectedConversion * 1000; // $1,000 por cliente
    
    return {
      potentialClients, 
      expectedConversion,
      financial
    };
  };
  
  // Si no hay datos disponibles, mostrar un estado de carga o error
  if (isLoading || isLoadingVariables) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Mapa de Calor - Segmentación de Clientes</h2>
        </div>
        <div className="flex justify-center items-center h-64">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-8 w-8 bg-prometeo-blue/50 rounded-full mb-2"></div>
            <div className="h-4 w-32 bg-gray-200 rounded mb-2"></div>
            <div className="h-3 w-48 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Mapa de Calor - Segmentación de Clientes</h2>
        </div>
        <div className="flex justify-center items-center h-64">
          <div className="flex flex-col items-center text-red-500">
            <AlertTriangle size={24} className="mb-2" />
            <div className="text-sm">Error al cargar los datos del mapa de calor</div>
            <button 
              onClick={() => refetch()} 
              className="mt-4 px-3 py-1 bg-prometeo-blue text-white text-xs rounded"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  // Si no hay datos después de cargar, mostrar mensaje
  if (!data || !data.x_categories || !data.y_categories) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-lg font-bold text-prometeo-black">Mapa de Calor - Segmentación de Clientes</h2>
        </div>
        <div className="flex justify-center items-center h-64">
          <div className="text-sm text-gray-500">No hay datos disponibles para esta visualización</div>
        </div>
      </div>
    );
  }
  
  // Obtener las categorías de los ejes, asegurando que estén ordenadas adecuadamente
  const xCategories = data.x_categories || [];
  const yCategories = data.y_categories || [];
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Mapa de Calor - Segmentación de Clientes</h2>
        <div className="flex items-center space-x-2">
          <button 
            className="text-gray-500 hover:text-prometeo-blue transition-colors"
            onClick={() => refetch()}
            title="Actualizar datos"
          >
            <RefreshCw size={16} />
          </button>
          <button className="text-gray-500 hover:text-prometeo-blue transition-colors">
            <Info size={18} />
          </button>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-4 mb-5">
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Eje X:</label>
          <select 
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={xAxis}
            onChange={(e) => setXAxis(e.target.value)}
          >
            {availableVariables.map(v => (
              <option key={v.value} value={v.value}>{v.label}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Eje Y:</label>
          <select 
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value)}
          >
            {availableVariables.map(v => (
              <option key={v.value} value={v.value}>{v.label}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Mostrar:</label>
          <select 
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={metric}
            onChange={(e) => setMetric(e.target.value as 'probability' | 'count')}
          >
            <option value="probability">Probabilidad</option>
            <option value="count">Número de Clientes</option>
          </select>
        </div>
      </div>
      
      <div className="flex mb-2">
        <div className="w-20"></div> {/* Spacer para etiquetas del eje Y */}
        <div className="flex-1 grid" style={{ gridTemplateColumns: `repeat(${xCategories.length}, 1fr)` }}>
          {xCategories.map(x => (
            <div key={x} className="text-center text-xs font-medium text-gray-600">
              {x}
            </div>
          ))}
        </div>
      </div>
      
      <div className="overflow-x-auto">
        {/* Mapa de calor */}
        {yCategories.map((y, yIndex) => (
          <div key={y} className="flex items-center mb-1">
            <div className="w-20 text-xs font-medium text-gray-600 text-right pr-2">
              {y}
            </div>
            <div className="flex-1 grid" style={{ gridTemplateColumns: `repeat(${xCategories.length}, 1fr)` }}>
              {xCategories.map((x, xIndex) => {
                const value = data.values[yIndex]?.[xIndex] || 0;
                
                return (
                  <div
                    key={`${x}-${y}`}
                    className={`h-12 flex items-center justify-center ${
                      metric === 'probability' ? getBackgroundColor(value) : 'bg-blue-100'
                    } relative`}
                    onMouseEnter={() => setHoveredCell({ x: xIndex, y: yIndex, value })}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    <span className={`text-sm font-medium ${
                      metric === 'probability' ? getTextColor(value) : 'text-gray-700'
                    }`}>
                      {formatCellValue(value, metric)}
                    </span>
                    
                    {/* Tooltip para oportunidad financiera */}
                    {hoveredCell && hoveredCell.x === xIndex && hoveredCell.y === yIndex && metric === 'probability' && (
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 bg-gray-800 text-white p-2 rounded text-xs z-10 w-48">
                        <div className="font-bold">Oportunidad financiera</div>
                        <div>Conversión esperada: {Math.round(value * 0.2 * (data.values[yIndex][xIndex] || 1))}</div>
                        <div>Valor potencial: ${Math.round(value * 0.2 * (data.values[yIndex][xIndex] || 1) * 1000).toLocaleString()}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 flex justify-between items-center">
        <div className="text-xs text-gray-500">
          <p>
            {metric === 'probability' 
              ? 'Mostrando probabilidad promedio por segmento.' 
              : 'Mostrando conteo de clientes por segmento.'
            }
          </p>
        </div>
        
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 bg-blue-100"></div>
          <div className="w-4 h-4 bg-blue-200"></div>
          <div className="w-4 h-4 bg-blue-300"></div>
          <div className="w-4 h-4 bg-blue-400"></div>
          <div className="w-4 h-4 bg-blue-500"></div>
          <span className="text-xs text-gray-500 ml-1">
            {metric === 'probability' ? 'Probabilidad' : 'Densidad'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default HeatMap;
