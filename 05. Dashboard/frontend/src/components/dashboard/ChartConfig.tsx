
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement, 
  Title, 
  Tooltip, 
  Legend, 
  Filler,
  type ChartOptions
} from 'chart.js';

// Register all the components we'll need for charts
export const registerCharts = () => {
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
  );
};

// Default chart options
export const defaultOptions: ChartOptions<'bar' | 'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        font: {
          family: 'Roboto'
        }
      }
    },
    title: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      titleFont: {
        family: 'Roboto',
        size: 13
      },
      bodyFont: {
        family: 'Roboto',
        size: 12
      },
      padding: 10,
      cornerRadius: 4
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: {
          family: 'Roboto',
          size: 11
        }
      }
    },
    y: {
      grid: {
        color: '#f0f0f0'
      },
      ticks: {
        font: {
          family: 'Roboto',
          size: 11
        }
      }
    }
  }
};
