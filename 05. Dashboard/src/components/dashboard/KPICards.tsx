import { TrendingUp, TrendingDown, Users, DollarSign, CheckCircle } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow';
  loading?: boolean;
}

const KPICard = ({ 
  title, 
  value, 
  description, 
  trend, 
  trendValue, 
  icon, 
  color = 'blue', 
  loading = false 
}: KPICardProps) => {
  
  const colorClasses = {
    blue: 'bg-prometeo-blue/10 text-prometeo-blue',
    green: 'bg-prometeo-green/10 text-prometeo-green',
    red: 'bg-prometeo-red/10 text-prometeo-red',
    yellow: 'bg-prometeo-yellow/10 text-prometeo-yellow',
  };

  const trendIcon = trend === 'up' ? (
    <TrendingUp size={16} className="text-prometeo-green" />
  ) : trend === 'down' ? (
    <TrendingDown size={16} className="text-prometeo-red" />
  ) : null;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      {loading ? (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-sm font-medium text-gray-500">{title}</h3>
            {icon && <div className={`p-2 rounded-full ${colorClasses[color]}`}>{icon}</div>}
          </div>
          <div className="flex items-baseline">
            <p className="text-2xl font-bold">{value}</p>
            {trend && trendValue && (
              <div className="flex items-center ml-2 text-xs">
                {trendIcon}
                <span className={trend === 'up' ? 'text-prometeo-green' : 'text-prometeo-red'}>
                  {trendValue}
                </span>
              </div>
            )}
          </div>
          {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
        </>
      )}
    </div>
  );
};

export const KPICards = () => {
  // Datos para cálculos
  const clientesData = {
    total: 1452,
    clientesPotenciales: 725, // Clientes con potencial de contratar un seguro
    conversionEsperada: 0.20, // 20% fijo como solicitado
    primaPorSeguro: 1000 // $1,000 USD por prima
  };

  // Número de clientes que se espera convertir (20% de los potenciales)
  const clientesConversion = Math.round(clientesData.clientesPotenciales * clientesData.conversionEsperada);
  
  // Calcular oportunidad financiera (20% de los potenciales * $1,000)
  const oportunidadFinanciera = clientesConversion * clientesData.primaPorSeguro;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <KPICard
        title="Clientes Potenciales"
        value={clientesData.clientesPotenciales.toLocaleString()}
        trend="up"
        trendValue="12%"
        icon={<Users size={18} />}
        color="blue"
        description="Clientes con probabilidad de contratar"
      />
      
      <KPICard
        title="Conversión Esperada"
        value={`${clientesConversion.toLocaleString()} clientes`}
        trend="up"
        trendValue="20%"
        icon={<TrendingUp size={18} />}
        color="green"
        description="20% de los clientes potenciales"
      />
      
      <KPICard
        title="Oportunidad Financiera"
        value={`$${oportunidadFinanciera.toLocaleString()}`}
        trend="up"
        trendValue="~"
        icon={<DollarSign size={18} />}
        color="yellow"
        description="Basado en prima de $1,000 USD"
      />
      
      <KPICard
        title="Progreso de Contactos"
        value="35.7%"
        trend="down"
        trendValue="5.1%"
        icon={<CheckCircle size={18} />}
        color="red"
        description="Meta mensual: 250 contactos"
      />
    </div>
  );
};

export default KPICards;
