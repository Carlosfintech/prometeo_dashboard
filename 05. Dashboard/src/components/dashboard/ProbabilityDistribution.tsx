
import { Bar } from 'react-chartjs-2';
import { Info } from 'lucide-react';
import { defaultOptions } from './ChartConfig';

export const ProbabilityDistribution = () => {
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

  // Sample data - would be fetched from API in a real application
  const labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'];
  
  const data = {
    labels,
    datasets: [
      {
        label: 'No Contactados',
        data: [145, 256, 367, 289, 210, 167, 134, 98, 65, 43],
        backgroundColor: 'rgba(30, 144, 255, 0.7)',
        barPercentage: 0.7,
      },
      {
        label: 'Contactados',
        data: [67, 102, 132, 178, 143, 112, 87, 54, 32, 21],
        backgroundColor: 'rgba(220, 220, 220, 0.7)',
        barPercentage: 0.7,
      },
    ],
  };

  // Simulate a threshold line by adding a custom plugin
  const thresholdPlugin = {
    id: 'thresholdLine',
    beforeDraw: (chart: any) => {
      if (!chart || !chart.scales || !chart.scales.x) return;
      
      const { ctx, chartArea, scales } = chart;
      // Umbral del 0.2389 o 23.89% - estaría entre la segunda y tercera barra
      // Find the position of the threshold (between 20-30%)
      try {
        const thresholdX = scales.x.getPixelForValue(2) + 
          (scales.x.getPixelForValue(3) - scales.x.getPixelForValue(2)) * 0.389;
        
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
        ctx.fillText('Umbral: 23.89%', thresholdX, chartArea.top - 10);
        ctx.restore();
      } catch (error) {
        console.error('Error drawing threshold line:', error);
      }
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
        <Bar 
          options={options} 
          data={data} 
          plugins={[thresholdPlugin]} 
        />
      </div>
      
      <div className="mt-4 text-xs text-gray-500">
        <p>El umbral óptimo de 23.89% se calculó basado en el punto de equilibrio entre costo de contacto y beneficio potencial.</p>
      </div>
    </div>
  );
};

export default ProbabilityDistribution;
