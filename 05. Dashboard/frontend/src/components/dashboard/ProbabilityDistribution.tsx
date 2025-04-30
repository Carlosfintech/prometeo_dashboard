import { Bar } from 'react-chartjs-2';
import { Info } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { defaultOptions } from './ChartConfig';

export const ProbabilityDistribution = () => {
  // Fetch distribution data
  const { data, isLoading, error } = useQuery<{ buckets: Array<{ range: string; no_contacted: number; contacted: number }>; threshold: number }>({
    queryKey: ['probDist'],
    queryFn: () => api.get('/metrics/probability-distribution').then(res => res.data),
    refetchOnWindowFocus: false,
  });
  
  // Loading and error
  if (isLoading) return <div>Loading distribution...</div>;
  if (error || !data) return <div>Error loading distribution</div>;
  
  // Transformar datos
  const labels = data.buckets.map(b => b.range);
  const noData = data.buckets.map(b => b.no_contacted);
  const yesData = data.buckets.map(b => b.contacted);
  const thresholdPct = data.threshold * 100;
  
  // Datos para el gráfico (ambas series siempre visibles)
  const chartData = {
    labels,
    datasets: [
      { label: 'No Contactados', data: noData, backgroundColor: 'rgba(30, 144, 255, 0.7)', barPercentage: 0.7 },
      { label: 'Contactados', data: yesData, backgroundColor: 'rgba(220, 220, 220, 0.7)', barPercentage: 0.7 }
    ]
  };

  // Configuración del chart
  const options = {
    ...defaultOptions,
    plugins: {
      ...defaultOptions.plugins,
      tooltip: {
        ...defaultOptions.plugins?.tooltip,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.raw} clientes`;
          }
        }
      }
    },
    scales: {
      ...defaultOptions.scales,
      x: {
        ...defaultOptions.scales?.x,
        title: {
          display: true,
          text: 'Probabilidad de Conversión (%)',
          color: '#666',
          font: {
            size: 12,
          },
          padding: { top: 10 }
        }
      },
      y: {
        ...defaultOptions.scales?.y,
        title: {
          display: true,
          text: 'Número de Clientes',
          color: '#666',
          font: {
            size: 12,
          },
          padding: { bottom: 10 }
        },
        beginAtZero: true
      }
    }
  };

  // Plugin para dibujar línea de umbral
  const thresholdPlugin = {
    id: 'thresholdLine',
    beforeDraw: (chart: any) => {
      if (!chart || !chart.scales || !chart.scales.x) return;
      
      const { ctx, chartArea, scales } = chart;
      
      // Ubicar línea en porcentaje
      const thresholdX = scales.x.getPixelForValue(thresholdPct);
      
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(thresholdX, chartArea.top);
      ctx.lineTo(thresholdX, chartArea.bottom);
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#DC3545';
      ctx.stroke();
      ctx.restore();
      
      // Draw label for threshold
      ctx.save();
      ctx.font = '12px Roboto';
      ctx.fillStyle = '#DC3545';
      ctx.textAlign = 'center';
      ctx.fillText(`Umbral: ${thresholdPct.toFixed(2)}%`, thresholdX, chartArea.top - 10);
      ctx.restore();
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex justify-between items-center mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Distribución de Probabilidades</h2>
        <button className="text-gray-500 hover:text-prometeo-blue transition-colors">
          <Info size={18} />
        </button>
      </div>
      
      <div className="h-80">
        <Bar options={options} data={chartData} plugins={[thresholdPlugin]} />
      </div>
      
      <div className="mt-4 text-xs text-gray-500">
        <p>El umbral óptimo de {thresholdPct.toFixed(2)}% se calculó basado en el punto de equilibrio entre costo de contacto y beneficio potencial.</p>
      </div>
    </div>
  );
};

export default ProbabilityDistribution;
