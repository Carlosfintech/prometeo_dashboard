import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { registerCharts } from './components/dashboard/ChartConfig'

// Register Chart.js components
registerCharts();

createRoot(document.getElementById("root")!).render(<App />);
