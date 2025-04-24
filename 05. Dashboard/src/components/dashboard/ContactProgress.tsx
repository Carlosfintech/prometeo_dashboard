import { TrendingUp, Edit, Save } from 'lucide-react';
import { useState } from 'react';

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
  const percentage = Math.round((value / total) * 100);
  
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
  // Sample data for demonstration - would come from API in real app
  const progressData = {
    contacts: {
      completed: 123,
      total: 345,
    },
    targets: {
      completion: 0.49,
      daysLeft: 14,
      daysInMonth: 30,
      targetGeneral: 250 // Meta general fija
    }
  };
  
  // Estado para la meta mensual editable en la sección de proyección
  const [monthlyTarget, setMonthlyTarget] = useState(200);
  const [isEditingTarget, setIsEditingTarget] = useState(false);
  const [tempTarget, setTempTarget] = useState(monthlyTarget.toString());
  
  // Calculate progress percentage
  const progressPercentage = Math.round((progressData.contacts.completed / progressData.contacts.total) * 100);
  
  // Calculate daily rate needed based on user-defined monthly target
  const dailyRateNeeded = Math.ceil((monthlyTarget - progressData.contacts.completed) / progressData.targets.daysLeft);
  
  // Determine progress status color
  const getStatusColor = (percentage: number) => {
    if (percentage < 33) return 'text-prometeo-red';
    if (percentage < 66) return 'text-prometeo-yellow';
    return 'text-prometeo-green';
  };
  
  // Handle monthly target change
  const handleTargetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (/^\d*$/.test(value)) { // Solo permitir dígitos
      setTempTarget(value);
    }
  };
  
  // Handle save of target
  const handleSaveTarget = () => {
    const newTarget = parseInt(tempTarget, 10);
    if (!isNaN(newTarget) && newTarget > 0) {
      setMonthlyTarget(newTarget);
    } else {
      setTempTarget(monthlyTarget.toString());
    }
    setIsEditingTarget(false);
  };
  
  // Calculate expected completion based on current rate
  const expectedCompletion = Math.min(100, Math.round((progressData.contacts.completed + (dailyRateNeeded * progressData.targets.daysLeft)) / progressData.contacts.total * 100));
  
  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-prometeo-black">Progreso de Contactos</h2>
      </div>
      
      <div className="mb-6">
        <div className="flex items-baseline justify-between mb-2">
          <div className="text-sm font-medium">
            Progreso General
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold ${getStatusColor(progressPercentage)}`}>
              {progressPercentage}%
            </span>
            <span className="text-xs text-gray-500">
              Meta: {progressData.targets.targetGeneral}
            </span>
          </div>
        </div>
        <ProgressBar 
          value={progressData.contacts.completed} 
          total={progressData.contacts.total} 
          color="bg-prometeo-blue" 
          height="h-6"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{progressData.contacts.completed} contactados</span>
          <span>{progressData.contacts.total} clientes prioritarios</span>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium">Proyección</h3>
          <div className="flex items-center">
            <div className="text-xs font-medium text-prometeo-yellow mr-2">
              {expectedCompletion}% esperado
            </div>
            <div className="flex items-center">
              <span className="text-xs text-gray-500 mr-1">Meta mensual:</span>
              {isEditingTarget ? (
                <div className="flex items-center">
                  <input
                    type="text"
                    value={tempTarget}
                    onChange={handleTargetChange}
                    className="w-16 px-1 py-0.5 text-xs border border-gray-300 rounded"
                    autoFocus
                  />
                  <button 
                    onClick={handleSaveTarget}
                    className="ml-1 text-prometeo-blue"
                  >
                    <Save size={14} />
                  </button>
                </div>
              ) : (
                <div className="flex items-center">
                  <span className="text-xs text-gray-700 font-medium">{monthlyTarget}</span>
                  <button 
                    onClick={() => setIsEditingTarget(true)}
                    className="ml-1 text-gray-400 hover:text-prometeo-blue"
                  >
                    <Edit size={12} />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <ProgressBar 
          value={expectedCompletion * progressData.contacts.total / 100} 
          total={progressData.contacts.total} 
          color="bg-prometeo-yellow" 
          showPercentage={false}
        />
        
        <div className="mt-3 text-xs text-gray-500">
          <span className="block">Faltan {progressData.targets.daysLeft} días para fin de mes</span>
          <span className="block">Ritmo necesario: {dailyRateNeeded} contactos/día</span>
          <span className="block mt-1">Avance actual: {Math.round(progressData.contacts.completed / monthlyTarget * 100)}% de la meta mensual</span>
        </div>
      </div>
    </div>
  );
};

export default ContactProgress;
