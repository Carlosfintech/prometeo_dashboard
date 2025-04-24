
import { useState } from 'react';
import { Info, RefreshCw } from 'lucide-react';

// Define the type for our heatmap data
type HeatMapData = {
  x: string;
  y: string;
  value: number;
  count: number;
}

export const HeatMap = () => {
  // State for axis selection
  const [xAxis, setXAxis] = useState('edad');
  const [yAxis, setYAxis] = useState('ingresos');
  const [showCount, setShowCount] = useState(false);
  
  // Mock data - would be fetched from API in real implementation
  const heatmapData: HeatMapData[] = [
    { x: '18-25', y: '0-1000', value: 0.15, count: 120 },
    { x: '18-25', y: '1001-2000', value: 0.22, count: 98 },
    { x: '18-25', y: '2001-3000', value: 0.31, count: 75 },
    { x: '18-25', y: '3001+', value: 0.38, count: 42 },
    { x: '26-35', y: '0-1000', value: 0.18, count: 142 },
    { x: '26-35', y: '1001-2000', value: 0.27, count: 156 },
    { x: '26-35', y: '2001-3000', value: 0.36, count: 118 },
    { x: '26-35', y: '3001+', value: 0.45, count: 87 },
    { x: '36-45', y: '0-1000', value: 0.21, count: 133 },
    { x: '36-45', y: '1001-2000', value: 0.32, count: 145 },
    { x: '36-45', y: '2001-3000', value: 0.42, count: 122 },
    { x: '36-45', y: '3001+', value: 0.53, count: 95 },
    { x: '46-55', y: '0-1000', value: 0.19, count: 105 },
    { x: '46-55', y: '1001-2000', value: 0.29, count: 125 },
    { x: '46-55', y: '2001-3000', value: 0.38, count: 92 },
    { x: '46-55', y: '3001+', value: 0.48, count: 73 },
    { x: '56+', y: '0-1000', value: 0.16, count: 89 },
    { x: '56+', y: '1001-2000', value: 0.25, count: 112 },
    { x: '56+', y: '2001-3000', value: 0.33, count: 68 },
    { x: '56+', y: '3001+', value: 0.41, count: 54 },
  ];
  
  // Get unique X and Y values
  const xValues = Array.from(new Set(heatmapData.map(item => item.x)));
  const yValues = Array.from(new Set(heatmapData.map(item => item.y))).reverse(); // Reverse for better visualization
  
  // Function to get color based on value (probability)
  const getBackgroundColor = (value: number) => {
    // Blue gradient from light to dark
    if (value < 0.2) return 'bg-blue-100';
    if (value < 0.3) return 'bg-blue-200';
    if (value < 0.4) return 'bg-blue-300';
    if (value < 0.5) return 'bg-blue-400';
    return 'bg-blue-500';
  };
  
  // Function to get text color based on background
  const getTextColor = (value: number) => {
    return value >= 0.4 ? 'text-white' : 'text-gray-700';
  };
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Mapa de Calor - Segmentación de Clientes</h2>
        <div className="flex items-center space-x-2">
          <button className="text-gray-500 hover:text-prometeo-blue transition-colors">
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
            <option value="edad">Edad</option>
            <option value="perfil">Perfil de Riesgo</option>
            <option value="region">Región</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Eje Y:</label>
          <select 
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value)}
          >
            <option value="ingresos">Ingresos</option>
            <option value="productos">Productos Actuales</option>
            <option value="antiguedad">Antigüedad</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Mostrar:</label>
          <select 
            className="border border-gray-300 rounded px-2 py-1 text-sm"
            value={showCount ? "count" : "probability"}
            onChange={(e) => setShowCount(e.target.value === "count")}
          >
            <option value="probability">Probabilidad</option>
            <option value="count">Número de Clientes</option>
          </select>
        </div>
      </div>
      
      <div className="flex mb-2">
        <div className="w-20"></div> {/* Spacer for y-axis labels */}
        <div className="flex-1 grid grid-cols-5">
          {xValues.map(x => (
            <div key={x} className="text-center text-xs font-medium text-gray-600">
              {x}
            </div>
          ))}
        </div>
      </div>
      
      <div className="overflow-x-auto">
        {yValues.map(y => (
          <div key={y} className="flex items-center mb-1">
            <div className="w-20 text-xs font-medium text-gray-600 text-right pr-2">
              {y}
            </div>
            <div className="flex-1 grid grid-cols-5 gap-1">
              {xValues.map(x => {
                const cell = heatmapData.find(item => item.x === x && item.y === y);
                return (
                  <div
                    key={`${x}-${y}`}
                    className={`h-12 flex items-center justify-center ${cell ? getBackgroundColor(cell.value) : 'bg-gray-100'}`}
                  >
                    {cell && (
                      <span className={`text-sm font-medium ${getTextColor(cell.value)}`}>
                        {showCount ? cell.count : `${(cell.value * 100).toFixed(0)}%`}
                      </span>
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
          <p>Mostrando probabilidad promedio de conversión por segmento.</p>
        </div>
        
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 bg-blue-100"></div>
          <div className="w-4 h-4 bg-blue-200"></div>
          <div className="w-4 h-4 bg-blue-300"></div>
          <div className="w-4 h-4 bg-blue-400"></div>
          <div className="w-4 h-4 bg-blue-500"></div>
          <span className="text-xs text-gray-500 ml-1">Probabilidad</span>
        </div>
      </div>
    </div>
  );
};

export default HeatMap;
